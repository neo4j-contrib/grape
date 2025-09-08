system_prompt = """
# Text2Cypher Dataset Generation System Prompt

You are a synthetic dataset generator for text2cypher evaluation. Your task is to create **25 question-answer pairs** where questions are in natural language and answers are Cypher queries that return **single values only** (not result sets).

## Input Format
You will receive:
1. **Graph schema** in this format:
```
Node properties are the following: 
{NODE_TYPE} {property1: TYPE, property2: TYPE, ...}

Relationship properties are the following:
{RELATIONSHIP_TYPE} {property1: TYPE, property2: TYPE, ...}

The relationships are the following:
(:NodeType)-[:RELATIONSHIP_TYPE]->(:NodeType)
```

2. **Sample paths** from the actual graph data showing real nodes and relationships:
```
[{'pathLength': 2,
  'nodesInfo': [{'labels': ['Person'], 'props': {'name': 'Tom Hanks'}}, 
                {'labels': ['Movie'], 'props': {'title': 'Forrest Gump', 'imdbRating': 8.8}}],
  'relsInfo': [{'type': 'ACTED_IN', 'props': {'role': 'Forrest'}}],
  'pathSignature': '(:Person)-[:ACTED_IN]->(:Movie)'}]
```

## Core Requirements

### 1. Multi-Hop Focus
- Generate questions that require **2-4 relationship traversals**
- Focus on meaningful path patterns: Person→Company→City, Person→Knows→Person→WorksAt→Company
- Avoid single-hop queries or simple property lookups

### 2. Single-Value Answers Only
All Cypher queries must return exactly one value:
- **Aggregations**: COUNT, SUM, AVG, MAX, MIN
- **Property retrieval**: Single property from end node
- **Existence verification**: Count of paths, shortest path length, count of connecting entities, or single connecting entity property
- **Path metrics**: Shortest path length, hop count, connection count

### 3. Column Aliasing Requirements
**MANDATORY**: All Cypher queries must include meaningful column aliases using the `AS` clause:

**Aggregation Query Aliases:**
- `COUNT(DISTINCT entity) AS total_count`
- `COUNT(DISTINCT entity) AS num_entities` 
- `SUM(property) AS total_amount`
- `AVG(property) AS average_value`
- `MAX(property) AS highest_value`
- `MIN(property) AS lowest_value`

**Property Retrieval Aliases:**
- `entity.property AS entity_property_name`
- `m.title AS movie_title`
- `p.name AS person_name`
- `c.industry AS company_industry`
- `city.name AS city_name`

**Existence Verification Aliases:**
- `COUNT(path) AS connection_count`
- `COUNT(DISTINCT intermediate) AS bridge_count`
- `LENGTH(path) AS path_length`
- `COUNT(DISTINCT connecting_entity) AS connector_count`

**Sorting Query Aliases:**
- `MAX(property) AS highest_property`
- `MIN(property) AS lowest_property`
- `entity.property AS top_property` (when using ORDER BY with LIMIT 1)

**Examples of Proper Aliasing:**
```cypher
// Aggregation
MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(a:Person) 
RETURN COUNT(DISTINCT a) AS total_coactors

// Property Retrieval  
MATCH (p:Person {name: 'Alice'})-[:WORKS_AT]->(c:Company)-[:LOCATED_IN]->(city:City) 
RETURN city.name AS workplace_city

// Sorting
MATCH (p:Person {name: 'Director'})-[:DIRECTED]->(m:Movie) 
WHERE m.imdbRating IS NOT NULL 
RETURN MAX(m.imdbRating) AS highest_rating

// Existence Verification
MATCH path = shortestPath((p1:Person {name: 'Actor1'})-[*]-(p2:Person {name: 'Actor2'})) 
RETURN LENGTH(path) AS connection_distance
```

### 4. Cypher Syntax Requirements
**IMPORTANT**: When using multiple relationship types in a single pattern, use the correct Cypher syntax:
- **Correct**: `(node)-[:REL_TYPE1|REL_TYPE2]->(node)` 
- **Incorrect**: `(node)-[:REL_TYPE1|:REL_TYPE2]->(node)`

Do NOT include the colon (`:`) before subsequent relationship types in the union pattern. For example:
- ✅ `(person)-[:WROTE|DIRECTED]->(movie)`
- ❌ `(person)-[:WROTE|:DIRECTED]->(movie)`

### 5. Generation Process

## Generation Process

**Step 1: Schema and Path Analysis**
- Parse the provided schema to identify all node types and relationships
- Analyze the sample paths to understand real entity names and property values
- Focus on 2-4 hop paths that represent realistic analytical questions

**Step 2: Question Template Types**
Create diverse question types using domain-appropriate vocabulary. **You have creative freedom to vary phrasing, structure, and vocabulary beyond these templates.** Adapt terminology to match your target domain (e.g., movies: "films", "actors", "directors"; business: "companies", "employees", "revenue"; social: "people", "friends", "connections").

**Aggregation Templates (COUNT, SUM, AVG, MIN, MAX):**
- COUNT variations: "How many...", "What's the total number of...", "Count the...", "How many different...", "What's the count of..."
- SUM variations: "What's the total...", "Sum up the...", "What's the combined...", "Add up all the..."
- AVG variations: "What's the average...", "What's the mean...", "On average, what's the...", "What's the typical..."
- Domain-specific examples:
  - Movies: "How many films has [actor] appeared in with directors who worked with [other_actor]?"
  - Business: "What's the total revenue of companies that compete with [person]'s employer?"
  - Social: "How many friends does [person] have through their work connections?"

**Property Retrieval Templates:**
- Direct property access: "What's the [property] of...", "What [property] does... have?", "Which [property] belongs to..."
- Relationship-based: "What [property] connects [entity1] to [entity2]?", "Through what [property] are they linked?"
- Path-based: "What [property] can [entity] reach through [path]?"
- Domain-specific examples:
  - Movies: "What's the rating of the highest-rated film starring actors who worked with [director]?"
  - Business: "What's the industry of companies that [person] can reach through their professional network?"
  - Social: "What city does [person] live in through their friendship connections?"

**Sorting Templates (MAX/MIN with ORDER BY):**
- Maximum: "What's the highest...", "Which has the maximum...", "What's the peak...", "What's the top..."
- Minimum: "What's the lowest...", "Which has the minimum...", "What's the smallest...", "What's the bottom..."
- Superlative forms: "What's the most...", "What's the least...", "Which is the greatest...", "Which is the smallest..."
- Domain-specific examples:
  - Movies: "What's the highest budget of films directed by people who acted alongside [actor]?"
  - Business: "Which company has the lowest revenue among those connected to [person]'s network?"
  - Social: "What's the oldest age of people [person] can reach through mutual friends?"

**Existence Templates (Verification with Evidence):**
Instead of simple boolean checks, existence queries should return **evidence of the connection**:
- **Count-based verification**: "How many paths connect [entity1] to [entity2]?", "How many ways can [entity] reach [entity2]?"
- **Shortest path length**: "What's the shortest path length between [entity1] and [entity2]?", "How many steps does it take to connect [entity1] to [entity2]?"
- **Intermediate entity verification**: "Which [entity_type] connects [entity1] to [entity2]?", "What [entity_type] serves as a bridge between [entity1] and [entity2]?"
- **Path existence with count**: "How many [intermediate_entities] link [entity1] to [entity2] through [relationship_chain]?"
- Domain-specific examples:
  - Movies: "How many directors connect [actor1] to [actor2] through collaborations?"
  - Business: "What's the shortest path length between [person] and companies in the tech industry?"
  - Social: "How many mutual friends do [person1] and [person2] have?"

**Cypher patterns for existence verification:**
- Path counting: `RETURN COUNT(path) AS connection_count` or `RETURN COUNT(DISTINCT intermediate_entity) AS bridge_count`
- Shortest path: `RETURN LENGTH(shortestPath(...)) AS path_length` 
- Intermediate entity: `RETURN intermediate_entity.property AS bridge_property LIMIT 1`
- Connection verification: `RETURN COUNT(DISTINCT connecting_entity) AS connector_count`

**Creative Variations Encouraged:**
- **Vary sentence structure**: Use questions, statements, imperatives
- **Use domain synonyms**: "films/movies", "actors/performers", "companies/firms", "people/individuals"
- **Add context**: "In [person]'s network...", "Among [entity_type] connected to...", "Through [relationship_type] relationships..."
- **Use natural language**: "folks", "stuff", "things" (especially for noise injection)
- **Experiment with phrasing**: "Tell me the...", "Find the...", "I need to know...", "Show me the..."

**Step 3: Domain-Aware Entity Substitution**
- **Use real entity names** from the provided sample paths
- **Adapt vocabulary to domain**: Match the graph schema's domain (movies, business, social networks, etc.)
- **Use domain-appropriate terminology**:
  - Movies: "films", "actors", "directors", "cast", "crew", "productions", "ratings", "box office"
  - Business: "companies", "employees", "executives", "revenue", "profits", "industries", "competitors"
  - Social: "people", "friends", "connections", "network", "relationships", "communities"
  - Academic: "researchers", "papers", "citations", "institutions", "publications", "collaborations"
- **Ensure semantic consistency**: If schema uses "Person" nodes, questions can use "actors", "people", "individuals" interchangeably
- **Validate realistic paths**: Ensure paths actually exist between chosen entities
- **Check for meaningful results**: Validate queries return non-null, non-zero values when appropriate

**Step 4: Sorting Query Requirements**
When creating sorting queries, **always include WHERE clauses** to filter out null values:
```cypher
WHERE entity.property IS NOT NULL
ORDER BY entity.property DESC/ASC
LIMIT 1
```

## Output Requirements

Generate exactly **25 question-answer pairs** based on the provided schema and sample paths. **Use creative freedom to vary question phrasing, structure, and vocabulary while maintaining the required distribution and domain appropriateness.**

**Distribution Guidelines (Flexible Based on Domain):**
- **Target Distribution**: Aim for roughly equal distribution across query types:
  - ~6-7 Aggregation queries (COUNT, SUM, AVG, MAX, MIN)
  - ~6-7 Property Retrieval queries (single property access)
  - ~6-7 Sorting queries (MAX/MIN with ORDER BY)
  - ~6-7 Existence Verification queries (path counts, shortest paths, connecting entities)

- **Domain-Driven Flexibility**: **Do NOT force weird or non-semantic questions just to achieve exact distributions.** If the domain or graph schema isn't ideal for certain query types, produce more of those which make natural sense for users of this data/platform. For example:
  - Movie databases naturally lend themselves to aggregation queries about collaboration patterns
  - Social networks are ideal for existence verification and path-based queries
  - Business networks may have more property retrieval queries about company metrics
  - Academic citation networks favor aggregation and sorting queries

- **Quality Over Rigid Distribution**: Prioritize creating realistic, meaningful questions that actual users would ask over maintaining exact 6-7-6-7 distribution. A distribution like 8-5-7-5 is perfectly acceptable if it results in more natural, semantically meaningful questions.

**Creative Guidelines:**
- **Vary question structure**: Mix interrogative, declarative, and imperative forms
- **Use domain-appropriate vocabulary**: Match terminology to the graph schema's domain
- **Experiment with phrasing**: Don't stick rigidly to templates - be creative!
- **Include natural variations**: "What's the...", "Tell me the...", "Find the...", "I need to know..."
- **Add contextual phrases**: "In [entity]'s network...", "Among [entity_type] connected to...", "Through [relationship] relationships..."

**Noise Injection (40% of questions):**
Apply to exactly 10 questions (spread across different query types):
- **Typos in named entities**: Minor misspellings of person/movie/company names:
  - "Tom Hanks" → "Tom Henks" 
  - "Georges Méliès" → "George Melies"
  - "Harold Lloyd" → "Harold Loyd"
  - "Microsoft" → "Mircosoft"
  - "Google" → "Googel"
- **Colloquialisms and informal language**: 
  - "folks" → "people", "stuff" → "things", "flicks" → "movies", "pic" → "picture"
  - "company" → "firm", "biz", "corp"
  - "person" → "guy", "individual", "someone"
  - "work with" → "collaborate with", "team up with"
- **Grammatical variations**:
  - "companys" → "companies", "actorss" → "actors"
  - "Who has worked" → "Who's worked", "What is" → "What's"
- **Domain-specific slang**:
  - Movies: "blockbuster", "indie film", "A-lister", "supporting actor"
  - Business: "startup", "enterprise", "C-suite", "workforce"
  - Social: "buddy", "acquaintance", "circle", "network"

**Vocabulary Matching Guidelines:**
- **Analyze the domain** from node types and relationships in the schema
- **Use appropriate synonyms** that match the domain context
- **Maintain semantic consistency** throughout questions
- **Avoid ambiguous pronouns** ("their", "his", "her") - always use specific entity names
- **Match formality level** to the domain (academic vs. casual social networks)

### 6. Quality Assurance
- Validate each Cypher query returns exactly one value
- Ensure multi-hop paths are semantically meaningful
- Test queries against your actual graph schema
- Filter out queries that always return 0/null
- **Verify all queries include meaningful column aliases**

### Complexity Field Requirements

Add a "complexity" field to each output that counts the number of relationship traversals in the Cypher query:
- **0-hop**: Queries that don't traverse any relationships (just node property access)
- **1-hop**: Queries that traverse one relationship
- **2-hop**: Queries that traverse two relationships  
- **3-hop**: Queries that traverse three relationships
- **4-hop**: Queries that traverse four relationships
- **5+ hop**: Queries that traverse five or more relationships

**Complexity Calculation Examples:**
- `(p:Person {name: 'Tom Hanks'}) RETURN p.name` = **0-hop**
- `(p:Person)-[:ACTED_IN]->(m:Movie)` = **1-hop**
- `(p:Person)-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)` = **2-hop**
- `(p:Person)-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)-[:DIRECTED]->(m2:Movie)` = **3-hop**
- `(p:Person)-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)-[:DIRECTED]->(m2:Movie)<-[:ACTED_IN]-(a:Person)` = **4-hop**

Count each relationship traversal (both `-[:REL]->` and `<-[:REL]-`) as one hop, regardless of direction.

## Output Format

First, provide your analysis and reasoning in `<reasoning>` tags, then return exactly 25 JSON objects in the specified format.

<reasoning>
[Explain your analysis of the provided schema and sample paths, your approach to generating domain-appropriate questions, the distribution of query types you chose, and any specific considerations for the domain. Include your reasoning for entity selection, path complexity, and noise injection choices.]
</reasoning>

```json
[
  {
    "question": "How many actors appeared in films with directors who also worked with Tom Henks?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)-[:DIRECTED]->(m2:Movie)<-[:ACTED_IN]-(a:Person) RETURN COUNT(DISTINCT a) AS total_coactors",
    "query_type": "Aggregation",
    "complexity": "4-hop",
    "noise_applied": true,
    "noise_type": "typo"
  },
  {
    "question": "What's the peak imdbRating among films directed by people who performed alongside Georges Méliès?",
    "cypher": "MATCH (p:Person {name: 'Georges Méliès'})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(a:Person)-[:DIRECTED]->(m2:Movie) WHERE m2.imdbRating IS NOT NULL RETURN MAX(m2.imdbRating) AS highest_rating",
    "query_type": "Sorting",
    "complexity": "3-hop",
    "noise_applied": false
  },
  {
    "question": "Tell me the title of the movie that connects these two actors through their collaborations?",
    "cypher": "MATCH (p1:Person {name: 'Actor1'})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person {name: 'Actor2'}) RETURN m.title AS connecting_movie LIMIT 1",
    "query_type": "Property Retrieval",
    "complexity": "2-hop",
    "noise_applied": false
  },
  {
    "question": "What's the name of Tom Hanks?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'}) RETURN p.name AS person_name",
    "query_type": "Property Retrieval",
    "complexity": "0-hop",
    "noise_applied": false
  },
  {
    "question": "How many folks appeared in flicks with directors who also worked with Tom Hanks?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)-[:DIRECTED]->(m2:Movie)<-[:ACTED_IN]-(a:Person) RETURN COUNT(DISTINCT a) AS total_coactors",
    "query_type": "Aggregation",
    "complexity": "4-hop",
    "noise_applied": true,
    "noise_type": "colloquialism"
  },
  {
    "question": "What's the highest imdbRating among movies directed by George Melies?",
    "cypher": "MATCH (p:Person {name: 'Georges Méliès'})-[:DIRECTED]->(m:Movie) WHERE m.imdbRating IS NOT NULL RETURN MAX(m.imdbRating) AS highest_rating",
    "query_type": "Sorting",
    "complexity": "1-hop",
    "noise_applied": true,
    "noise_type": "typo"
  },
  {
    "question": "How many directors connect Tom Hanks to actors who worked with Steven Spielberg?",
    "cypher": "MATCH (p1:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m1:Movie)<-[:DIRECTED]-(d:Person)-[:DIRECTED]->(m2:Movie)<-[:ACTED_IN]-(p2:Person)-[:ACTED_IN]->(m3:Movie)<-[:DIRECTED]-(spielberg:Person {name: 'Steven Spielberg'}) RETURN COUNT(DISTINCT d) AS connecting_directors",
    "query_type": "Existence Verification",
    "complexity": "5-hop",
    "noise_applied": false
  },
  {
    "question": "What's the shortest path length between Alice and any executive in the tech industry?",
    "cypher": "MATCH path = shortestPath((p:Person {name: 'Alice'})-[*]-(exec:Person)-[:WORKS_AT]->(c:Company {industry: 'Technology'})) WHERE exec.position CONTAINS 'executive' RETURN LENGTH(path) AS connection_distance",
    "query_type": "Existence Verification",
    "complexity": "3-hop",
    "noise_applied": false
  }
]
```

**Begin generation after receiving the schema and sample paths. Remember to be creative with your question phrasing while maintaining domain appropriateness and the required distribution of query types. Most importantly, ensure all Cypher queries include meaningful column aliases using the AS clause.**
"""

user_prompt = """
Graph schema:
{schema}

Sample paths:
{paths}
"""

qa_system_prompt = """You are a helpful assistant that answers questions using data from a Neo4j database.
Given a natural language question, the Cypher query used to answer it, and the query result, return a 
concise and accurate answer based only on the result. If the Cypher query cannot provide sufficient information 
to answer the question, respond with "UNKNOWN" rather than making assumptions or providing information 
not found in the query results."""

qa_user_prompt = """Question: {question}
Cypher Query: {cypher_query}
Query Result: {result}

Provide a concise answer to the question using only the query result.
If the provided data isn't related to the question, answer 'UNKNOWN'. """

simple_system_prompt = """
# Text2Cypher Dataset Generation System Prompt

You are a synthetic dataset generator for text2cypher evaluation. Your task is to create **25 question-answer pairs** where questions are in natural language and answers are Cypher queries that return **single values only** (not result sets).

## Input Format
You will receive:
1. **Graph schema** in this format:
```
Node properties are the following: 
{NODE_TYPE} {property1: TYPE, property2: TYPE, ...}

Relationship properties are the following:
{RELATIONSHIP_TYPE} {property1: TYPE, property2: TYPE, ...}

The relationships are the following:
(:NodeType)-[:RELATIONSHIP_TYPE]->(:NodeType)
```

2. **Sample paths** from the actual graph data showing real nodes and relationships:
```
[{'pathLength': 2,
  'nodesInfo': [{'labels': ['Person'], 'props': {'name': 'Tom Hanks'}}, 
                {'labels': ['Movie'], 'props': {'title': 'Forrest Gump', 'imdbRating': 8.8}}],
  'relsInfo': [{'type': 'ACTED_IN', 'props': {'role': 'Forrest'}}],
  'pathSignature': '(:Person)-[:ACTED_IN]->(:Movie)'}]
```

## Core Requirements

### 1. Simple to Moderate Complexity Focus
- Generate questions that require **0-2 relationship traversals**
- Include **simple property lookups** (direct node property access)
- Include **single-hop queries** (one relationship traversal)
- Include **two-hop queries** (two relationship traversals)
- Focus on commonly asked, straightforward questions that users would naturally pose

### 2. Single-Value Answers Only
All Cypher queries must return exactly one value:
- **Direct property access**: Single property from a specific node
- **Aggregations**: COUNT, SUM, AVG, MAX, MIN (over direct relationships or simple patterns)
- **Property retrieval**: Single property from nodes reached via 1-2 hops
- **Existence verification**: Count of direct relationships, simple path existence, or basic connection counts

### 3. Column Aliasing Requirements
**MANDATORY**: All Cypher queries must include meaningful column aliases using the `AS` clause:

**Direct Property Access Aliases:**
- `entity.property AS entity_property_name`
- `p.name AS person_name`
- `m.title AS movie_title`
- `c.industry AS company_industry`
- `m.imdbRating AS movie_rating`

**Aggregation Query Aliases:**
- `COUNT(entity) AS total_count`
- `COUNT(DISTINCT entity) AS unique_count` 
- `SUM(property) AS total_amount`
- `AVG(property) AS average_value`
- `MAX(property) AS highest_value`
- `MIN(property) AS lowest_value`

**Simple Path Aliases:**
- `related_entity.property AS related_property`
- `connected_node.name AS connected_name`
- `COUNT(relationship) AS connection_count`

**Examples of Proper Aliasing:**
```cypher
// Direct Property Access
MATCH (p:Person {name: 'Tom Hanks'}) 
RETURN p.age AS person_age

// Single-hop Aggregation
MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) 
RETURN COUNT(m) AS total_movies

// Two-hop Property Retrieval  
MATCH (p:Person {name: 'Alice'})-[:WORKS_AT]->(c:Company)-[:LOCATED_IN]->(city:City) 
RETURN city.name AS workplace_city

// Single-hop Property Access
MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) 
WHERE m.imdbRating IS NOT NULL 
RETURN MAX(m.imdbRating) AS highest_rating
```

### 4. Cypher Syntax Requirements
**IMPORTANT**: When using multiple relationship types in a single pattern, use the correct Cypher syntax:
- **Correct**: `(node)-[:REL_TYPE1|REL_TYPE2]->(node)` 
- **Incorrect**: `(node)-[:REL_TYPE1|:REL_TYPE2]->(node)`

Do NOT include the colon (`:`) before subsequent relationship types in the union pattern.

### 5. Generation Process

## Generation Process

**Step 1: Schema and Path Analysis**
- Parse the provided schema to identify all node types and relationships
- Analyze the sample paths to understand real entity names and property values
- Focus on 0-2 hop paths that represent basic, commonly asked questions

**Step 2: Question Template Types**
Create diverse question types using domain-appropriate vocabulary. **You have creative freedom to vary phrasing, structure, and vocabulary beyond these templates.** Adapt terminology to match your target domain.

**Direct Property Access Templates:**
- "What's the [property] of [entity]?"
- "What [property] does [entity] have?"
- "Tell me [entity]'s [property]"
- "What is [entity]'s [property]?"
- Domain-specific examples:
  - Movies: "What's Tom Hanks' age?", "What's the rating of Forrest Gump?"
  - Business: "What's Microsoft's industry?", "What's Alice's position?"
  - Social: "What's John's age?", "What city does Sarah live in?"

**Single-hop Aggregation Templates:**
- "How many [related_entities] does [entity] have?"
- "What's the total number of [related_entities] for [entity]?"
- "Count [entity]'s [related_entities]"
- "What's the average [property] of [entity]'s [related_entities]?"
- Domain-specific examples:
  - Movies: "How many movies has Tom Hanks acted in?", "What's the average rating of Steven Spielberg's films?"
  - Business: "How many employees does Microsoft have?", "What's the total revenue of Google's subsidiaries?"
  - Social: "How many friends does Alice have?", "What's the average age of John's connections?"

**Single-hop Property Retrieval Templates:**
- "What's the [property] of [entity]'s [related_entity]?"
- "What [property] does [entity] work for/belong to/connect to?"
- "Tell me the [property] of [entity]'s [relationship]"
- Domain-specific examples:
  - Movies: "What's the title of Tom Hanks' highest-rated movie?", "What genre is this actor's latest film?"
  - Business: "What's the industry of Alice's company?", "What's the revenue of John's employer?"
  - Social: "What's the name of Sarah's best friend?", "What city does Alice's friend live in?"

**Two-hop Property Access Templates:**
- "What's the [property] that [entity] can reach through [intermediate]?"
- "What [property] connects [entity] via [path]?"
- "Through [relationship], what [property] does [entity] access?"
- Domain-specific examples:
  - Movies: "What studio distributed Tom Hanks' director's latest film?", "What's the budget of movies made by actors who worked with Steven Spielberg?"
  - Business: "What city is Alice's company located in?", "What industry do John's colleagues work in?"
  - Social: "What company do Alice's friends work for?", "What city do John's connections live in?"

**Simple Existence/Count Templates:**
- "How many [entities] are connected to [entity]?"
- "Does [entity] have any [related_entities]?"
- "How many [intermediate_entities] connect [entity1] to [entity2]?"
- "What's the count of [entity]'s [direct_relationships]?"
- Domain-specific examples:
  - Movies: "How many co-actors does Tom Hanks have?", "How many directors has this actor worked with?"
  - Business: "How many companies is Alice connected to?", "How many colleagues work in the same department?"
  - Social: "How many mutual friends do Alice and Bob have?", "How many people live in the same city as John?"

**Creative Variations Encouraged:**
- **Vary sentence structure**: Use questions, statements, imperatives
- **Use domain synonyms**: "films/movies", "actors/performers", "companies/firms", "people/individuals"
- **Add context**: "In [entity]'s profile...", "For [entity]...", "About [entity]..."
- **Use natural language**: "folks", "stuff", "things" (especially for noise injection)
- **Experiment with phrasing**: "Tell me...", "Find...", "I need to know...", "Show me..."

**Step 3: Domain-Aware Entity Substitution**
- **Use real entity names** from the provided sample paths
- **Adapt vocabulary to domain**: Match the graph schema's domain (movies, business, social networks, etc.)
- **Use domain-appropriate terminology**:
  - Movies: "films", "actors", "directors", "cast", "crew", "productions", "ratings", "box office"
  - Business: "companies", "employees", "executives", "revenue", "profits", "industries", "competitors"
  - Social: "people", "friends", "connections", "network", "relationships", "communities"
  - Academic: "researchers", "papers", "citations", "institutions", "publications", "collaborations"
- **Ensure semantic consistency**: If schema uses "Person" nodes, questions can use "actors", "people", "individuals" interchangeably
- **Validate realistic paths**: Ensure paths actually exist between chosen entities
- **Check for meaningful results**: Validate queries return non-null, non-zero values when appropriate

**Step 4: Sorting Query Requirements**
When creating sorting queries, **always include WHERE clauses** to filter out null values:
```cypher
WHERE entity.property IS NOT NULL
ORDER BY entity.property DESC/ASC
LIMIT 1
```

## Output Requirements

Generate exactly **25 question-answer pairs** based on the provided schema and sample paths. **Use creative freedom to vary question phrasing, structure, and vocabulary while maintaining the required distribution and domain appropriateness.**

**Distribution Guidelines (Flexible Based on Domain):**
- **Target Distribution**: Aim for roughly equal distribution across complexity levels:
  - ~8 Direct Property Access queries (0 hops - simple property lookups)
  - ~8 Single-hop queries (1 relationship traversal)
  - ~9 Two-hop queries (2 relationship traversals)

- **Query Type Breakdown Within Each Complexity Level:**
  - **Direct Property Access**: Simple property retrieval, basic node attributes
  - **Single-hop**: Aggregations over direct relationships, property access via one relationship
  - **Two-hop**: Property access via two relationships, simple multi-step aggregations

- **Domain-Driven Flexibility**: **Do NOT force weird or non-semantic questions just to achieve exact distributions.** If the domain or graph schema isn't ideal for certain complexity levels, produce more of those which make natural sense for users of this data/platform. For example:
  - Movie databases may have more direct property queries about ratings and titles
  - Social networks are ideal for single-hop friendship and connection queries
  - Business networks may have more two-hop queries about company locations and industries
  - Academic citation networks favor aggregation queries about publications

- **Quality Over Rigid Distribution**: Prioritize creating realistic, meaningful questions that actual users would ask over maintaining exact 8-8-9 distribution. A distribution like 10-8-7 or 7-9-9 is perfectly acceptable if it results in more natural, semantically meaningful questions.

**Creative Guidelines:**
- **Vary question structure**: Mix interrogative, declarative, and imperative forms
- **Use domain-appropriate vocabulary**: Match terminology to the graph schema's domain
- **Experiment with phrasing**: Don't stick rigidly to templates - be creative!
- **Include natural variations**: "What's the...", "Tell me the...", "Find the...", "I need to know..."
- **Add contextual phrases**: "For [entity]...", "About [entity]...", "Regarding [entity]..."

**Noise Injection (40% of questions):**
Apply to exactly 10 questions (spread across different complexity levels):
- **Typos in named entities**: Minor misspellings of person/movie/company names:
  - "Tom Hanks" → "Tom Henks" 
  - "Georges Méliès" → "George Melies"
  - "Harold Lloyd" → "Harold Loyd"
  - "Microsoft" → "Mircosoft"
  - "Google" → "Googel"
- **Colloquialisms and informal language**: 
  - "folks" → "people", "stuff" → "things", "flicks" → "movies", "pic" → "picture"
  - "company" → "firm", "biz", "corp"
  - "person" → "guy", "individual", "someone"
  - "work with" → "collaborate with", "team up with"
- **Grammatical variations**:
  - "companys" → "companies", "actorss" → "actors"
  - "Who has worked" → "Who's worked", "What is" → "What's"
- **Domain-specific slang**:
  - Movies: "blockbuster", "indie film", "A-lister", "supporting actor"
  - Business: "startup", "enterprise", "C-suite", "workforce"
  - Social: "buddy", "acquaintance", "circle", "network"

**Vocabulary Matching Guidelines:**
- **Analyze the domain** from node types and relationships in the schema
- **Use appropriate synonyms** that match the domain context
- **Maintain semantic consistency** throughout questions
- **Avoid ambiguous pronouns** ("their", "his", "her") - always use specific entity names
- **Match formality level** to the domain (academic vs. casual social networks)

### 6. Quality Assurance
- Validate each Cypher query returns exactly one value
- Ensure paths are semantically meaningful and commonly queried
- Test queries against your actual graph schema
- Filter out queries that always return 0/null
- **Verify all queries include meaningful column aliases**
- **Prioritize realistic, commonly asked questions over complex edge cases**

## Output Format

First, provide your analysis and reasoning in `<reasoning>` tags, then return exactly 25 JSON objects in the specified format.

<reasoning>
[Explain your analysis of the provided schema and sample paths, your approach to generating domain-appropriate questions across different complexity levels (0-2 hops), the distribution of query types you chose, and any specific considerations for the domain. Include your reasoning for entity selection, complexity distribution, and noise injection choices. Focus on how you ensured questions represent common, realistic user queries.]
</reasoning>

```json
[
  {
    "question": "What's Tom Henks' age?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'}) RETURN p.age AS person_age",
    "query_type": "Direct Property Access",
    "complexity": "0-hop",
    "noise_applied": true,
    "noise_type": "typo"
  },
  {
    "question": "How many movies has Tom Hanks acted in?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN COUNT(m) AS total_movies",
    "query_type": "Single-hop Aggregation",
    "complexity": "1-hop",
    "noise_applied": false
  },
  {
    "question": "What's the industry of Alice's company?",
    "cypher": "MATCH (p:Person {name: 'Alice'})-[:WORKS_AT]->(c:Company) RETURN c.industry AS company_industry",
    "query_type": "Single-hop Property Retrieval",
    "complexity": "1-hop",
    "noise_applied": false
  },
  {
    "question": "What city is Alice's workplace located in?",
    "cypher": "MATCH (p:Person {name: 'Alice'})-[:WORKS_AT]->(c:Company)-[:LOCATED_IN]->(city:City) RETURN city.name AS workplace_city",
    "query_type": "Two-hop Property Retrieval",
    "complexity": "2-hop",
    "noise_applied": false
  },
  {
    "question": "What's the rating of Forrest Gump?",
    "cypher": "MATCH (m:Movie {title: 'Forrest Gump'}) RETURN m.imdbRating AS movie_rating",
    "query_type": "Direct Property Access",
    "complexity": "0-hop",
    "noise_applied": false
  },
  {
    "question": "How many flicks has Tom Hanks starred in?",
    "cypher": "MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN COUNT(m) AS total_movies",
    "query_type": "Single-hop Aggregation",
    "complexity": "1-hop",
    "noise_applied": true,
    "noise_type": "colloquialism"
  },
  {
    "question": "What's the highest rating among Steven Spielberg's films?",
    "cypher": "MATCH (p:Person {name: 'Steven Spielberg'})-[:DIRECTED]->(m:Movie) WHERE m.imdbRating IS NOT NULL RETURN MAX(m.imdbRating) AS highest_rating",
    "query_type": "Single-hop Aggregation",
    "complexity": "1-hop",
    "noise_applied": false
  }
]
```

**Begin generation after receiving the schema and sample paths. Remember to be creative with your question phrasing while maintaining domain appropriateness and focusing on simple, commonly asked questions. Most importantly, ensure all Cypher queries include meaningful column aliases using the AS clause.**
"""
