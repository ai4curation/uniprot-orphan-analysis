# GO coverage on curated equivalent records

Retrieved 2026-11-01T22:46:37.636766+00:00 to 2026-11-01T22:47:58.576078+00:00; UniProt release 2026_03. QuickGO dataset release unavailable.

Compared **18** manually assessed equivalent pairs; current Swiss-Prot status, exact taxonomy and reference-proteome membership verified for every pair.

Orphan accessions have **110** distinct canonical annotation support rows: **48 non-IEA**, including **41 experimental-code rows**.

**48 non-IEA support rows** have no exact support counterpart; **41** carry experimental codes. Of these, **37 non-IEA rows** (**32 experimental**) lack even an exact assertion match, regardless of evidence.

## Comparison definitions

An assertion matches GO ID, qualifier/relation (including NOT), annotation extension, and ND/no-data status. Evidence support additionally matches GO and ECO evidence codes, reference, WITH/FROM and assigned-by. Accession and date are excluded from cross-record comparisons. Repeated support rows differing only in date collapse to the latest date. Group boundaries in WITH/FROM and extensions are preserved; list order is ignored.

This is an exact-match audit, without ontology ancestor/descendant inference. No exact match does not establish missing biological coverage, a curation error, or annotation loss. Non-IEA includes computational and phylogenetic evidence and ND; it is not synonymous with experimental evidence. Same assertions can have different evidence. Different WITH/FROM or assigned-by values also produce support differences; see `same_code_reference` in the annotation table for a less strict evidence comparison.

Isoform annotations are retained separately, not mapped between proteins without an explicit isoform correspondence (0 excluded rows). Fresh QuickGO data is used for both sides; historical mixed-date GOA caches and reviewer-proposed annotations are not inputs. The original manually assessed equivalence is not reassessed by this GO audit, and no annotations are transferred.

## Evidence codes

| Code | Orphan rows | Counterpart rows | Orphan support unmatched | Orphan rows without assertion match |
|---|---:|---:|---:|---:|
| EXP | 14 | 0 | 14 | 9 |
| IBA | 0 | 10 | 0 | 0 |
| IDA | 13 | 0 | 13 | 9 |
| IEA | 62 | 59 | 18 | 8 |
| IMP | 1 | 0 | 1 | 1 |
| IPI | 13 | 0 | 13 | 13 |
| ISS | 4 | 0 | 4 | 2 |
| TAS | 3 | 0 | 3 | 3 |

## Equivalent pairs

| Gene | Preferred Swiss-Prot | Counterpart | Rows (orphan / counterpart) | Shared assertions | Orphan-only assertions | Non-IEA support unmatched | Experimental rows without assertion match |
|---|---|---|---:|---:|---:|---:|---:|
| CHLRE/CP12 | [A6Q0K5](https://www.uniprot.org/uniprotkb/A6Q0K5/entry) | [A0A2K3DI03](https://www.uniprot.org/uniprotkb/A0A2K3DI03/entry) | 11 / 2 | 1 | 6 | 10 | 7 |
| FULFL/AVR4 | [Q00363](https://www.uniprot.org/uniprotkb/Q00363/entry) | [L7YE01](https://www.uniprot.org/uniprotkb/L7YE01/entry) | 10 / 2 | 2 | 4 | 8 | 6 |
| MOOTH/acsD | [Q07341](https://www.uniprot.org/uniprotkb/Q07341/entry) | [A0A1D7XAJ1](https://www.uniprot.org/uniprotkb/A0A1D7XAJ1/entry) | 5 / 1 | 1 | 2 | 4 | 4 |
| FULFL/AVR9 | [P22287](https://www.uniprot.org/uniprotkb/P22287/entry) | [L7YER9](https://www.uniprot.org/uniprotkb/L7YER9/entry) | 5 / 0 | 0 | 2 | 5 | 3 |
| MEDTR/DMI1 | [Q6RHR6](https://www.uniprot.org/uniprotkb/Q6RHR6/entry) | [G7IN96](https://www.uniprot.org/uniprotkb/G7IN96/entry) | 7 / 3 | 3 | 1 | 4 | 3 |
| MEDTR/NORK | [Q8L4H4](https://www.uniprot.org/uniprotkb/Q8L4H4/entry) | [A9YWR7](https://www.uniprot.org/uniprotkb/A9YWR7/entry) | 9 / 8 | 4 | 3 | 4 | 3 |
| PENCH/aatA | [P15802](https://www.uniprot.org/uniprotkb/P15802/entry) | [A0ABQ8WFJ5](https://www.uniprot.org/uniprotkb/A0ABQ8WFJ5/entry) | 9 / 3 | 3 | 2 | 6 | 2 |
| THLAR/TFP | [G1FNI6](https://www.uniprot.org/uniprotkb/G1FNI6/entry) | [A0AAU9R9U8](https://www.uniprot.org/uniprotkb/A0AAU9R9U8/entry) | 8 / 5 | 5 | 2 | 3 | 2 |
| DERPT/Derp2 | [P49278](https://www.uniprot.org/uniprotkb/P49278/entry) | [A0ABQ8J715](https://www.uniprot.org/uniprotkb/A0ABQ8J715/entry) | 5 / 3 | 3 | 1 | 2 | 2 |
| POPTR/PAL | [P45730](https://www.uniprot.org/uniprotkb/P45730/entry) | [A0A2K1XD28](https://www.uniprot.org/uniprotkb/A0A2K1XD28/entry) | 7 / 6 | 5 | 1 | 1 | 0 |
| STECR/nas-8 | [D2KBH9](https://www.uniprot.org/uniprotkb/D2KBH9/entry) | [A0A4U8UYW6](https://www.uniprot.org/uniprotkb/A0A4U8UYW6/entry) | 6 / 5 | 5 | 0 | 1 | 0 |
| POPTR/CCOAOMT1 | [O65862](https://www.uniprot.org/uniprotkb/O65862/entry) | [A0A2K1Z5Q2](https://www.uniprot.org/uniprotkb/A0A2K1Z5Q2/entry) | 3 / 2 | 2 | 1 | 0 | 0 |
| POPTR/CCOAOMT2 | [O65922](https://www.uniprot.org/uniprotkb/O65922/entry) | [A0A2K2C664](https://www.uniprot.org/uniprotkb/A0A2K2C664/entry) | 3 / 2 | 2 | 1 | 0 | 0 |
| POPTR/MAOX | [P34105](https://www.uniprot.org/uniprotkb/P34105/entry) | [B9ILT5](https://www.uniprot.org/uniprotkb/B9ILT5/entry) | 7 / 7 | 5 | 2 | 0 | 0 |
| POPTR/PRX2 | [A9PCL4](https://www.uniprot.org/uniprotkb/A9PCL4/entry) | [B9ILP9](https://www.uniprot.org/uniprotkb/B9ILP9/entry) | 5 / 11 | 5 | 0 | 0 | 0 |
| THLAR/CYP71B1 | [P49264](https://www.uniprot.org/uniprotkb/P49264/entry) | [A0AAU9RUE5](https://www.uniprot.org/uniprotkb/A0AAU9RUE5/entry) | 4 / 4 | 4 | 0 | 0 | 0 |
| THLAR/matK | [Q9GF35](https://www.uniprot.org/uniprotkb/Q9GF35/entry) | [A0A1U9RZH7](https://www.uniprot.org/uniprotkb/A0A1U9RZH7/entry) | 4 / 4 | 4 | 0 | 0 | 0 |
| TOXGO/SAG1 | [P13664](https://www.uniprot.org/uniprotkb/P13664/entry) | [A0A7J6K396](https://www.uniprot.org/uniprotkb/A0A7J6K396/entry) | 2 / 1 | 1 | 1 | 0 | 0 |

## Non-IEA support requiring comparison

These are source database annotations, not new assertions endorsed by this analysis. Repeated term/reference rows may have different WITH/FROM partners; AND groups and OR alternatives remain distinct. Full annotation extensions and assigned-by values are retained in the CSV.

| Gene | GO term | Relation | Evidence | Reference | WITH/FROM | Exact assertion on counterpart? | Same code/reference? |
|---|---|---|---|---|---|---|---|
| CHLRE/CP12 | [GO:0005507](https://www.ebi.ac.uk/QuickGO/term/GO:0005507) copper ion binding | enables | IDA | [PMID:16259044](https://pubmed.ncbi.nlm.nih.gov/16259044/) | — | no | no |
| CHLRE/CP12 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:12846565](https://pubmed.ncbi.nlm.nih.gov/12846565/) | UniProtKB:P19824 AND UniProtKB:P50362 | no | no |
| CHLRE/CP12 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:24863370](https://pubmed.ncbi.nlm.nih.gov/24863370/) | UniProtKB:P19824 | no | no |
| CHLRE/CP12 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:24863370](https://pubmed.ncbi.nlm.nih.gov/24863370/) | UniProtKB:P50362 | no | no |
| CHLRE/CP12 | [GO:0009507](https://www.ebi.ac.uk/QuickGO/term/GO:0009507) chloroplast | located_in | IDA | [PMID:12846565](https://pubmed.ncbi.nlm.nih.gov/12846565/) | — | no | no |
| CHLRE/CP12 | [GO:0009507](https://www.ebi.ac.uk/QuickGO/term/GO:0009507) chloroplast | located_in | ISS | GO_REF:0000024 | UniProtKB:O22914 | no | no |
| CHLRE/CP12 | [GO:0016151](https://www.ebi.ac.uk/QuickGO/term/GO:0016151) nickel cation binding | enables | IDA | [PMID:16259044](https://pubmed.ncbi.nlm.nih.gov/16259044/) | — | no | no |
| CHLRE/CP12 | [GO:0019899](https://www.ebi.ac.uk/QuickGO/term/GO:0019899) enzyme binding | enables | IPI | [PMID:12846565](https://pubmed.ncbi.nlm.nih.gov/12846565/) | UniProtKB:P50362 | no | no |
| CHLRE/CP12 | [GO:0032991](https://www.ebi.ac.uk/QuickGO/term/GO:0032991) protein-containing complex | part_of | ISS | GO_REF:0000024 | UniProtKB:O22914 | no | no |
| CHLRE/CP12 | [GO:0080153](https://www.ebi.ac.uk/QuickGO/term/GO:0080153) negative regulation of reductive pentose-phosphate cycle | involved_in | ISS | GO_REF:0000024 | UniProtKB:O22914 | yes | no |
| DERPT/Derp2 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:19060881](https://pubmed.ncbi.nlm.nih.gov/19060881/) | UniProtKB:O00206-1 | no | no |
| DERPT/Derp2 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:19060881](https://pubmed.ncbi.nlm.nih.gov/19060881/) | UniProtKB:Q9Y6Y9 | no | no |
| FULFL/AVR4 | [GO:0008061](https://www.ebi.ac.uk/QuickGO/term/GO:0008061) chitin binding | enables | EXP | [PMID:30148881](https://pubmed.ncbi.nlm.nih.gov/30148881/) | — | yes | no |
| FULFL/AVR4 | [GO:0080185](https://www.ebi.ac.uk/QuickGO/term/GO:0080185) effector-mediated activation of plant hypersensitive response by symbiont | involved_in | EXP | [PMID:10998185](https://pubmed.ncbi.nlm.nih.gov/10998185/) | — | no | no |
| FULFL/AVR4 | [GO:0080185](https://www.ebi.ac.uk/QuickGO/term/GO:0080185) effector-mediated activation of plant hypersensitive response by symbiont | involved_in | EXP | [PMID:16167771](https://pubmed.ncbi.nlm.nih.gov/16167771/) | — | no | no |
| FULFL/AVR4 | [GO:0140320](https://www.ebi.ac.uk/QuickGO/term/GO:0140320) PAMP receptor decoy activity | enables | EXP | [PMID:30148881](https://pubmed.ncbi.nlm.nih.gov/30148881/) | — | no | no |
| FULFL/AVR4 | [GO:0140403](https://www.ebi.ac.uk/QuickGO/term/GO:0140403) effector-mediated suppression of host innate immune response | involved_in | IMP | [PMID:30148881](https://pubmed.ncbi.nlm.nih.gov/30148881/) | — | no | no |
| FULFL/AVR4 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | EXP | [PMID:23716655](https://pubmed.ncbi.nlm.nih.gov/23716655/) | — | no | no |
| FULFL/AVR4 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | EXP | [PMID:9437864](https://pubmed.ncbi.nlm.nih.gov/9437864/) | — | no | no |
| FULFL/AVR4 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | TAS | [PMID:25902074](https://pubmed.ncbi.nlm.nih.gov/25902074/) | — | no | no |
| FULFL/AVR9 | [GO:0080185](https://www.ebi.ac.uk/QuickGO/term/GO:0080185) effector-mediated activation of plant hypersensitive response by symbiont | involved_in | EXP | [PMID:10998185](https://pubmed.ncbi.nlm.nih.gov/10998185/) | — | no | no |
| FULFL/AVR9 | [GO:0080185](https://www.ebi.ac.uk/QuickGO/term/GO:0080185) effector-mediated activation of plant hypersensitive response by symbiont | involved_in | EXP | [PMID:16167771](https://pubmed.ncbi.nlm.nih.gov/16167771/) | — | no | no |
| FULFL/AVR9 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | EXP | [PMID:26946045](https://pubmed.ncbi.nlm.nih.gov/26946045/) | — | no | no |
| FULFL/AVR9 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | TAS | [PMID:25902074](https://pubmed.ncbi.nlm.nih.gov/25902074/) | — | no | no |
| FULFL/AVR9 | [GO:0140404](https://www.ebi.ac.uk/QuickGO/term/GO:0140404) effector-mediated perturbation of host innate immune response by symbiont | involved_in | TAS | [PMID:9437864](https://pubmed.ncbi.nlm.nih.gov/9437864/) | — | no | no |
| MEDTR/DMI1 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:27230377](https://pubmed.ncbi.nlm.nih.gov/27230377/) | UniProtKB:A0A072VMJ3 | no | no |
| MEDTR/DMI1 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:27230377](https://pubmed.ncbi.nlm.nih.gov/27230377/) | UniProtKB:G7IBJ4 | no | no |
| MEDTR/DMI1 | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:27230377](https://pubmed.ncbi.nlm.nih.gov/27230377/) | UniProtKB:G7JND3 | no | no |
| MEDTR/DMI1 | [GO:0031965](https://www.ebi.ac.uk/QuickGO/term/GO:0031965) nuclear membrane | located_in | EXP | [PMID:27230377](https://pubmed.ncbi.nlm.nih.gov/27230377/) | — | yes | no |
| MEDTR/NORK | [GO:0004672](https://www.ebi.ac.uk/QuickGO/term/GO:0004672) protein kinase activity | enables | IDA | [PMID:26839127](https://pubmed.ncbi.nlm.nih.gov/26839127/) | — | yes | no |
| MEDTR/NORK | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:26839127](https://pubmed.ncbi.nlm.nih.gov/26839127/) | UniProtKB:E4NKF8 | no | no |
| MEDTR/NORK | [GO:0046777](https://www.ebi.ac.uk/QuickGO/term/GO:0046777) protein autophosphorylation | involved_in | IDA | [PMID:26839127](https://pubmed.ncbi.nlm.nih.gov/26839127/) | — | no | no |
| MEDTR/NORK | [GO:0106310](https://www.ebi.ac.uk/QuickGO/term/GO:0106310) protein serine kinase activity | enables | EXP | [PMID:26839127](https://pubmed.ncbi.nlm.nih.gov/26839127/) | — | no | no |
| MOOTH/acsD | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:22419154](https://pubmed.ncbi.nlm.nih.gov/22419154/) | UniProtKB:Q07340 | no | no |
| MOOTH/acsD | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:22419154](https://pubmed.ncbi.nlm.nih.gov/22419154/) | UniProtKB:Q07340 | no | no |
| MOOTH/acsD | [GO:0005515](https://www.ebi.ac.uk/QuickGO/term/GO:0005515) protein binding | enables | IPI | [PMID:22419154](https://pubmed.ncbi.nlm.nih.gov/22419154/) | UniProtKB:Q46389 | no | no |
| MOOTH/acsD | [GO:0015977](https://www.ebi.ac.uk/QuickGO/term/GO:0015977) carbon fixation | involved_in | IDA | [PMID:22419154](https://pubmed.ncbi.nlm.nih.gov/22419154/) | — | no | no |
| PENCH/aatA | [GO:0005782](https://www.ebi.ac.uk/QuickGO/term/GO:0005782) peroxisomal matrix | is_active_in | IDA | [PMID:18439860](https://pubmed.ncbi.nlm.nih.gov/18439860/) | — | no | no |
| PENCH/aatA | [GO:0042318](https://www.ebi.ac.uk/QuickGO/term/GO:0042318) penicillin biosynthetic process | acts_upstream_of_or_within | IDA | [PMID:1368505](https://pubmed.ncbi.nlm.nih.gov/1368505/) | — | no | no |
| PENCH/aatA | [GO:0042318](https://www.ebi.ac.uk/QuickGO/term/GO:0042318) penicillin biosynthetic process | involved_in | IDA | [PMID:2120195](https://pubmed.ncbi.nlm.nih.gov/2120195/) | — | yes | no |
| PENCH/aatA | [GO:0050640](https://www.ebi.ac.uk/QuickGO/term/GO:0050640) isopenicillin-N N-acyltransferase activity | enables | EXP | [PMID:1368505](https://pubmed.ncbi.nlm.nih.gov/1368505/) | — | yes | no |
| PENCH/aatA | [GO:0050640](https://www.ebi.ac.uk/QuickGO/term/GO:0050640) isopenicillin-N N-acyltransferase activity | enables | EXP | [PMID:2110531](https://pubmed.ncbi.nlm.nih.gov/2110531/) | — | yes | no |
| PENCH/aatA | [GO:0050640](https://www.ebi.ac.uk/QuickGO/term/GO:0050640) isopenicillin-N N-acyltransferase activity | enables | IDA | [PMID:2120195](https://pubmed.ncbi.nlm.nih.gov/2120195/) | — | yes | no |
| POPTR/PAL | [GO:0045548](https://www.ebi.ac.uk/QuickGO/term/GO:0045548) phenylalanine ammonia-lyase activity | enables | ISS | GO_REF:0000024 | UniProtKB:P24481 | yes | no |
| STECR/nas-8 | [GO:0004222](https://www.ebi.ac.uk/QuickGO/term/GO:0004222) metalloendopeptidase activity | enables | EXP | [PMID:20670659](https://pubmed.ncbi.nlm.nih.gov/20670659/) | — | yes | no |
| THLAR/TFP | [GO:0019760](https://www.ebi.ac.uk/QuickGO/term/GO:0019760) glucosinolate metabolic process | involved_in | IDA | [PMID:26260516](https://pubmed.ncbi.nlm.nih.gov/26260516/) | — | yes | no |
| THLAR/TFP | [GO:0042802](https://www.ebi.ac.uk/QuickGO/term/GO:0042802) identical protein binding | enables | IDA | [PMID:26260516](https://pubmed.ncbi.nlm.nih.gov/26260516/) | — | no | no |
| THLAR/TFP | [GO:0042803](https://www.ebi.ac.uk/QuickGO/term/GO:0042803) protein homodimerization activity | enables | IDA | [PMID:26260516](https://pubmed.ncbi.nlm.nih.gov/26260516/) | — | no | no |

[Pair counts](pairs.csv) · [All annotation comparisons](annotations.csv) · [Evidence counts](evidence-counts.csv) · [Provenance and source hashes](provenance.json)

API documentation: [QuickGO](https://www.ebi.ac.uk/QuickGO/api/index.html). Raw responses are retained in the sibling `sources/` directory.
