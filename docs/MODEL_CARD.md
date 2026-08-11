# Model Card

- **Base Model**: Qwen2.5 (intended)
- **Training Strategy**: LoRA/QLoRA via Unsloth.
- **Intended Use**: Generating constructive code review comments for PR diffs.
- **Limitations**: The model may hallucinate fixes for complex architectural issues. It is best used for identifying stylistic, minor logical, or best-practice violations.
