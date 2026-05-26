
# Provenance (PROV-O)

A provenance trace records **how the project results were produced**. This makes the workflow easier to audit, understand and reproduce.

## Files

* `provenance/sample_run_prov.ttl` — machine-readable PROV-O trace.
* `provenance/sample_run_summary.md` — human-readable summary.
* `results/pipeline.log` — pipeline execution log, copied as a run artifact.

## PROV-O model

The provenance model describes three main elements:

| Element         | Meaning                            | Examples                                                                              |
| --------------- | ---------------------------------- | ------------------------------------------------------------------------------------- |
| `prov:Agent`    | Who or what performed the work     | Group 7, Python pipeline, Grobid, embedding model, NER model                          |
| `prov:Entity`   | Inputs and outputs used or created | corpus, config, abstracts, topics, similarity results, entities, grants, KG, RO-Crate |
| `prov:Activity` | Processing steps in the workflow   | PDF parsing, topic modeling, similarity computation, NER extraction, KG construction  |

## Relations used

| Relation                                     | Meaning                                    |
| -------------------------------------------- | ------------------------------------------ |
| `prov:used`                                  | An activity used an input                  |
| `prov:wasGeneratedBy`                        | An output was produced by an activity      |
| `prov:wasDerivedFrom`                        | An output was derived from another entity  |
| `prov:wasAssociatedWith`                     | An activity was linked to an agent         |
| `prov:hadPlan` / `prov:qualifiedAssociation` | Connects an activity to its script or plan |

## Example

```turtle
res:activity/topic-modeling a prov:Activity ;
    prov:used res:entity/abstracts ;
    prov:wasAssociatedWith res:agent/pipeline, res:agent/embedding-model, res:agent/group7 .

res:entity/topics prov:wasGeneratedBy res:activity/topic-modeling ;
    prov:wasDerivedFrom res:entity/abstracts .
```

This means that the **topic modeling activity** used the abstracts, was associated with the pipeline, embedding model and Group 7, and generated the topic results.



