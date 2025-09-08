import asyncio
import json

import json_repair
import re
from datetime import datetime

import pandas as pd
import neo4j

from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
from langchain_anthropic import ChatAnthropic
from langchain_neo4j import Neo4jGraph
from CyVer import SchemaValidator

from typing import Any

from prompts import (
    system_prompt,
    user_prompt,
    qa_system_prompt,
    qa_user_prompt
)

def convert_datetime(obj):
    if isinstance(obj, (pd.Timestamp, datetime, neo4j.time.DateTime, neo4j.time.Date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def _value_sanitize(d):
    """Sanitize the input dictionary or list.

    Sanitizes the input by removing embedding-like values,
    lists with more than 128 elements, that are mostly irrelevant for
    generating answers in a LLM context. These properties, if left in
    results, can occupy significant context space and detract from
    the LLM's performance by introducing unnecessary noise and cost.

    Args:
        d (Any): The input dictionary or list to sanitize.

    Returns:
        Any: The sanitized dictionary or list.
    """
    if isinstance(d, dict):
        new_dict = {}
        for key, value in d.items():
            if isinstance(value, dict):
                sanitized_value = _value_sanitize(value)
                if (
                    sanitized_value is not None
                ):  # Check if the sanitized value is not None
                    new_dict[key] = sanitized_value
            elif isinstance(value, list):
                if len(value) < 56:
                    sanitized_value = _value_sanitize(value)
                    if (
                        sanitized_value is not None
                    ):  # Check if the sanitized value is not None
                        new_dict[key] = sanitized_value
                # Do not include the key if the list is oversized
            else:
                new_dict[key] = value
        return new_dict
    elif isinstance(d, list):
        if len(d) < 56:
            return [
                _value_sanitize(item) for item in d if _value_sanitize(item) is not None
            ]
        else:
            return None
    else:
        return d
    
def extract_json_from_markdown(text: str):
    """
    Extracts and parses JSON content wrapped between ```json and ``` markers.

    Parameters:
    text (str): Input string containing JSON in markdown code block format.

    Returns:
    object or None: Parsed JSON object if found and valid, else None.
    """
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json_repair.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return None
    else:
        try:
            return json_repair.loads(text)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
    return None

sampling_query = """// Collect sample nodes with different labels for diversity
MATCH (n)
WITH labels(n) as labelSet, collect(n)[0] as sampleNode
ORDER BY size(labelSet) DESC, rand()
WITH collect(sampleNode) as sampleNodes

// Generate paths from diverse starting points
UNWIND sampleNodes[0..15] as startNode
CALL (startNode) {
    // Get shorter paths
    MATCH p1=(startNode)-[*2..3]-()
    RETURN p1 as p
    LIMIT 2
    UNION ALL
    // Get longer paths
    WITH startNode  
    MATCH p2=()-[*3..4]->(startNode)
    RETURN p2 as p
    LIMIT 2
}
// Deduplicate and enrich path information
WITH DISTINCT p
WITH p,
    nodes(p) as pathNodes,
    relationships(p) as pathRels,
    length(p) as pathLength

RETURN 
    pathLength,
    [node in pathNodes | {labels: labels(node), props: properties(node)}] as nodesInfo,
    [rel in pathRels | {type: type(rel), props: properties(rel)}] as relsInfo,
    // Create a human-readable path signature
    reduce(s = "", i in range(0, length(p) + 1) | 
        s + 
        CASE 
            WHEN i % 2 = 0 
            THEN "(:" + labels(nodes(p)[i/2])[0] + ")"
            ELSE "-[:" + type(relationships(p)[(i-1)/2]) + "]->"
        END
    ) + "(:" + labels(nodes(p)[-1])[0] + ")" as pathSignature
ORDER BY pathLength DESC, rand()
LIMIT 25"""

def validate_cypher(schema_validator, query, database_name):
    schema_score, schema_metadata = schema_validator.validate(query, database_name=database_name)
    if schema_score == 1.0:
        return True
    else:
        return False


def create_graph_connection(credential: str, db_url: str) -> Neo4jGraph:
    """Create and return a Neo4j graph connection."""
    return Neo4jGraph(
        url=db_url,
        username=credential,
        password=credential,
        database=credential,
        timeout=90
    )


def generate_qa_pairs(graph: Neo4jGraph, model: ChatAnthropic, system_prompt: str) -> list:
    """Generate question-answer pairs using the LLM and graph data."""
    paths = _value_sanitize(graph.query(sampling_query))
    messages = [
        ("system", system_prompt),
        ("human", user_prompt.format(schema=graph.schema, paths=paths)),
    ]
    response = model.invoke(messages, max_tokens=25000)
    return extract_json_from_markdown(response.content)


def validate_and_execute_record(record: dict, schema_validator: SchemaValidator, 
                               graph: Neo4jGraph, credential: str) -> dict:
    """Validate Cypher query and execute it, updating the record with results."""
    # Validate against schema
    record["validated"] = validate_cypher(schema_validator, record["cypher"], credential)
    
    if not record["validated"]:
        return record
    
    # Execute query and handle exceptions
    try:
        response = graph.query(record["cypher"])
        record["result"] = response
        
        # Check if result meets criteria (single non-empty, non-zero value)
        if not response or len(response) > 1:
            record["validated"] = False
            
    except Exception:
        record["validated"] = False
    
    return record


def process_database(credential: str, db_url: str, model: Any, 
                    iterations_per_database: int,
                    system_prompt: str = system_prompt) -> list:
    """Process a single database and return all generated records."""
    graph = create_graph_connection(credential, db_url)
    schema_validator = SchemaValidator(graph._driver)
    database_output = []
    
    for i in tqdm(range(iterations_per_database), 
                  desc=f"Iterations for {credential}", 
                  leave=False):
        try:
            # Generate QA pairs
            data = generate_qa_pairs(graph, model, system_prompt)
            # Validate and execute each record
            for record in data:
                # Add model name
                record["model"] = model._llm_type
                # Add database name
                record["database"] = credential
                validated_record = validate_and_execute_record(
                    record, schema_validator, graph, credential
                )
                database_output.append(validated_record)
        except:
            raise
            continue
    
    return database_output

async def process_example(example, qa_model):
    """Process a single example asynchronously"""
    if not example.get('validated'):
        return  # Skip unvalidated examples
    
    qa_messages = [
        ("system", qa_system_prompt),
        ("human", qa_user_prompt.format(
            question=example['question'], 
            cypher_query=example['cypher'], 
            result=example['result']
        )),
    ]
    
    answer = await qa_model.ainvoke(qa_messages)
    example['answer'] = answer.content  # Modify original dict in-place

# Main concurrent processing
async def process_all_examples(data, qa_model):
    """Process all examples concurrently with progress bar"""
    tasks = [
        process_example(example, qa_model)
        for example in data
    ]
    
    # Execute all tasks concurrently with progress bar
    await tqdm_asyncio.gather(*tasks, desc="Generating text answers")

# Alternative with semaphore for rate limiting
async def process_all_examples_with_limit(data, qa_model, max_concurrent=10):
    """Process all examples concurrently with a limit on concurrent requests"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(example):
        async with semaphore:
            await process_example(example, qa_model)
    
    tasks = [process_with_semaphore(example) for example in data]
    await tqdm_asyncio.gather(*tasks, desc="Processing examples")
