# Pinecone

The `Pinecone` class is an open-source vector database designed to store, query, and manage vector embeddings efficiently.

## Configuration

To use the Pinecone vector database, you need to configure it in your YAML configuration file.

You have to set API key for authentication with the Pinecone service.
You can get the API key from [here](https://app.pinecone.io/organizations/-/keys).

### Example YAML file

```yaml
- name: openai_pinecone
  db_type: pinecone
  embedding_model: openai_embed_3_large
  index_name: openai_embed_3_large
  api_key: ${PINECONE_API_KEY}
  similarity_metric: cosine
  dimension: 1536
```

Here is a simple example of a YAML configuration file that uses the Pinecone vector database and the OpenAI:

```yaml
vectordb:
  - name: openai_pinecone
    db_type: pinecone
    embedding_model: openai_embed_3_large
    index_name: openai_embed_3_large
    api_key: ${PINECONE_API_KEY}
    similarity_metric: cosine
    dimension: 1536
node_lines:
- node_line_name: retrieve_node_line  # Arbitrary node line name
  nodes:
    - node_type: semantic_retrieval
      strategy:
        metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
      top_k: 3
      modules:
        - module_type: vectordb
          vectordb: openai_pinecone
- node_line_name: post_retrieve_node_line  # Arbitrary node line name
  nodes:
    - node_type: prompt_maker
      strategy:
        metrics: [bleu, meteor, rouge]
      modules:
        - module_type: fstring
          prompt: "Read the passages and answer the given question. \n Question: {query} \n Passage: {retrieved_contents} \n Answer : "
    - node_type: generator
      strategy:
        metrics: [bleu, rouge]
      modules:
        - module_type: llama_index_llm
          llm: openai
          model: [ gpt-4o-mini ]
```

### Parameters

1. `embedding_model: str`
   - Purpose: Specifies the name or identifier of the embedding model to be used.
   - Example: "openai_embed_3_large"
   - Note: This should correspond to a valid embedding model that your system can use to generate vector embeddings. For more information see [custom your embedding model](https://marker-inc-korea.github.io/AutoRAG/local_model.html#configure-the-embedding-model) documentation.

2. `index_name: str`
   - Purpose: Sets the name of the Pinecone index where the vectors will be stored.
   - Example: "my_vector_index"
   - Note: If the index doesn't exist, it will be created. If it exists, it will be loaded.

3. `embedding_batch: int = 100`
   - Purpose: Determines the number of embeddings to process in a single batch.
   - Default: 100
   - Note: Adjust this based on your system's memory and processing capabilities. Larger batches may be faster but require more memory.

4. `dimension: int = 1536`
   - Purpose: Specifies the dimension of the vector embeddings.
   - Default: 1536
   - Note: This should correspond to the dimension of the embeddings generated by the specified embedding model.

5. `similarity_metric: str = "cosine"`
   - Purpose: Specifies the metric used to calculate similarity between vectors.
   - Default: "cosine"
   - Options: "cosine", "l2" (Euclidean distance), "ip" (Inner Product)
   - Note: Choose the metric that best suits your use case and data characteristics.

6. `cloud: str = "aws"`
    - Purpose: Specifies the cloud provider where the Pinecone service is hosted.
    - Default: "aws"
    - Options: "aws", "gcp", "azure"
    - Note: You can see full information at [here](https://docs.pinecone.io/guides/indexes/understanding-indexes#serverless-indexes)

7. `region: str = "us-east-1"`
   - Purpose: Specifies the region where the Pinecone service is hosted.
   - Default: "us-east-1"
   - Note: You can see full information at [here](https://docs.pinecone.io/guides/indexes/understanding-indexes#serverless-indexes)

8. `api_key: str = ""`
   - Purpose: The API key for authentication with the Pinecone.
   - Note:

9. `deletion_protection: str = "disabled"`
   - Purpose: Specifies whether deletion protection is enabled for the Pinecone index.
   - Default: "disabled"
   - Options: "enabled", "disabled"
   - Note: When enabled, the index cannot be deleted. This is useful for preventing accidental data loss.

10. `namespace: str = "default"`
    - Purpose: Specifies the namespace where the Pinecone index is located.
    - Default: "default"
    - Note: Namespaces are used to organize indexes within a Pinecone account.

11. `ingest_batch: int = 200`
    - Purpose: Determines the number of embeddings to ingest in a single batch.
    - Default: 200
    - Note: Pinecone tier limits the number of embeddings that can be ingested per second. Adjust this based on your system's capabilities.

## Usage

Here's a brief overview of how to use the main functions of the Pinecone vector database:

1. **Adding Vectors**:
   ```python
   await pinecone_db.add(ids, texts)
   ```
   This method adds new vectors to the database. It takes a list of IDs and corresponding texts, generates embeddings, and inserts them into the Pinecone Index.

2. **Querying**:
   ```python
   ids, scores = await pinecone_db.query(queries, top_k)
   ```
   Performs a similarity search on the stored vectors.
   It returns the IDs and their scores.
   Below you can see how the score is determined.

3. **Fetching Vectors**:
   ```python
   vectors = await pinecone_db.fetch(ids)
   ```
   Retrieves the vectors associated with the given IDs.

4. **Checking Existence**:
   ```python
   exists = await pinecone_db.is_exist(ids)
   ```
   Checks if the given IDs exist in the database.

5. **Deleting Vectors**:
   ```python
   await pinecone_db.delete(ids)
   ```
   Deletes the vectors associated with the given IDs from the database.

6. **Deleting the Collection**:
   ```python
   pinecone_db.delete_collection()
   ```
   Deletes the collection from the Pinecone server.
