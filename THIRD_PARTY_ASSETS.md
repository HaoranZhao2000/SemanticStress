# Source images and annotations

SemanticStress was derived from GQA and Visual Genome annotations. This repository includes derived captions, box coordinates, source identifiers, and image URLs. It does not redistribute the full image collection or the upstream annotation archives.

- [GQA downloads](https://cs.stanford.edu/people/dorarad/gqa/download.html)
- [Visual Genome project and data](https://visualgenome.org/)

`scripts/prepare_images.py` downloads the source images from the URLs listed in `data/image_sources_n446.jsonl` and adds box labels locally. The README teaser includes one illustrative source-image thumbnail. The repository's MIT license covers its code and original documentation; it does not supersede third-party image rights or upstream dataset terms. Users are responsible for checking those terms before downloading, using, or redistributing the images and derived records. Source URLs may change or become unavailable.
