namespace task10;

using Microsoft.Extensions.VectorData;

public class Docs
{
    [VectorStoreRecordKey]
    public Guid Id { get; set; } 

    [VectorStoreRecordData(IsFullTextSearchable = true, StoragePropertyName = "content")]
    public string Content { get; set; }

    [VectorStoreRecordVector(3072, DistanceFunction.EuclideanDistance, IndexKind.Hnsw, StoragePropertyName = "docs_embedding")]
    public ReadOnlyMemory<float>? Embedding { get; set; }
}