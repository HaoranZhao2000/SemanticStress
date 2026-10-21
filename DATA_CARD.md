# Dataset notes

SemanticStress contains 446 four-caption ladders: 124 object, 118 attribute-binding, 82 compositional-binding, and 122 spatial-relation examples. Each ladder uses one image and a fixed inventory of six grounded facts. Three cumulative pair swaps produce contradiction doses 0, 2, 4, and 6.

Each line of `data/ladders_n446.jsonl` is one ladder. `captions` stores the four candidate texts; `doses` stores their contradiction counts. `boxes` contains labeled rectangles, and `image_path` names the labeled image produced by `scripts/prepare_images.py`. `source_image_path` names the downloaded image without labels. Paths are relative to the repository root.

The candidates were derived from GQA and Visual Genome annotations. A five-person panel discussed all 465 candidates together and retained 446. This was a joint review, not five independent ratings. The release does not contain individual review records, excluded candidates, or agreement estimates. Review reduces obvious defects but cannot guarantee that every source annotation or ladder is error-free.

The dataset is intended for evaluating how models respond to controlled increases in image-grounded contradiction. It is not designed for training or for measuring a universal, equal-interval notion of caption difficulty. The four factors differ in content and may differ in difficulty even at the same dose. Box labels are part of the reference-resolution interface.

Source image files are downloaded separately and remain subject to upstream rights and terms. See `THIRD_PARTY_ASSETS.md`.
