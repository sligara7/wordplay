# LLM Analyzer Tool - Usage Guide

## Overview

The LLM Analyzer uses word graph analysis to detect quality issues in LLM-generated text. It's like a "linter" for language model output.

## Quick Start

```bash
# Analyze LLM output
python3 src/llm_analyzer.py your_llm_output.txt

# Compare to human baseline
python3 src/llm_analyzer.py your_llm_output.txt -r reference_corpus.txt

# Save detailed analysis
python3 src/llm_analyzer.py your_llm_output.txt -o analysis.json
```

## Example: Detecting Mode Collapse

**Good LLM Output:**
```
Health Score: 100/100
  Status: ✓ HEALTHY
Vocabulary size: 118 words
✓ No issues detected!
```

**Bad LLM Output (Mode Collapse):**
```
Health Score: 50/100
  Status: ✗ PROBLEMATIC
Vocabulary size: 20 words

Issues Detected:
  1. 🔴 SEVERE_MODE_COLLAPSE (critical)
     Severely limited vocabulary: only 20 unique words
     → Increase temperature, use top-p/top-k sampling

  2. 🟠 EXCESSIVE_REPETITION (high)
     Excessive repetition: 33 cycles detected
     → Reduce repetition penalty or use no-repeat-ngram-size

  3. 🔵 HUB_CONCENTRATION (low)
     Few words dominate connections: ['system', 'very']
```

## Issues Detected

### 1. Mode Collapse
**Symptoms:**
- Very limited vocabulary (<50 unique words)
- Same words repeated constantly
- Lack of diversity in expression

**Causes:**
- Temperature too low
- Overly conservative sampling
- Model not properly trained

**Fixes:**
```python
# Increase temperature
output = model.generate(temperature=1.0)  # was 0.7

# Use top-p sampling
output = model.generate(top_p=0.9, temperature=0.8)

# Add diversity penalty
output = model.generate(diversity_penalty=1.5)
```

### 2. Excessive Repetition
**Symptoms:**
- Many cycles in word graph
- Repetitive phrases
- Circular reasoning

**Causes:**
- Repetition penalty too low/high
- No n-gram blocking
- Training data has repetition

**Fixes:**
```python
# Add n-gram blocking
output = model.generate(no_repeat_ngram_size=3)

# Adjust repetition penalty
output = model.generate(repetition_penalty=1.2)

# Use frequency penalty
output = model.generate(frequency_penalty=0.5)
```

### 3. Sparse Transitions
**Symptoms:**
- Very low graph density
- Words don't connect naturally
- Stilted, unnatural language

**Causes:**
- Overly conservative sampling
- Poor training data
- Model uncertainty

**Fixes:**
```python
# Increase top-k
output = model.generate(top_k=100)  # was 50

# Adjust temperature
output = model.generate(temperature=0.9)
```

### 4. Excessive Dead Ends
**Symptoms:**
- Many words that never lead to others
- Truncated sentences
- Incomplete thoughts

**Causes:**
- Max length too short
- Early stopping too aggressive
- Model struggles to continue

**Fixes:**
```python
# Increase max length
output = model.generate(max_length=512)  # was 256

# Adjust stopping criteria
output = model.generate(
    max_length=512,
    min_length=100  # Ensure minimum
)
```

### 5. Disconnected Graph
**Symptoms:**
- Multiple separate components
- Topic jumping
- Lack of coherence

**Causes:**
- No context memory
- Poor prompt
- Model confusion

**Fixes:**
```python
# Better prompt with context
prompt = "Continue this story about [topic]: [context]"

# Use longer context window
output = model.generate(max_length=1024, context_window=2048)
```

### 6. Hub Concentration
**Symptoms:**
- Few words dominate (high centrality)
- Overuse of common words
- Lack of specificity

**Causes:**
- Training data imbalance
- Model defaults to common words
- Uncertainty about specifics

**Fixes:**
```python
# Reduce common words probability
output = model.generate(presence_penalty=0.5)

# Encourage diversity
output = model.generate(diversity_penalty=1.0)
```

## Health Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| 80-100 | ✓ HEALTHY | High-quality output, no major issues |
| 60-79 | ⚠ NEEDS ATTENTION | Some issues, may need tuning |
| 0-59 | ✗ PROBLEMATIC | Significant issues, fix before use |

## Comparison Metrics

### Orthogonality (Vocabulary Difference)
```
0.0 - 0.3: Very similar (same domain/topic)
0.3 - 0.7: Somewhat different (related domains)
0.7 - 1.0: Very different (orthogonal topics)
```

**Example:**
```
LLM output vs Human baseline: 0.896 orthogonality
→ LLM using very different vocabulary than humans
→ May indicate training data mismatch or mode collapse
```

### Structural Comparison
```
Density:     How interconnected words are
Avg Degree:  Average transitions per word

Good: Similar to reference
Bad:  Much higher/lower than reference
```

## Real-World Examples

### Example 1: Detecting Training Data Issues

```bash
# Generate samples from your model
python your_model.py --generate 1000 > model_samples.txt

# Analyze
python3 src/llm_analyzer.py model_samples.txt -r human_corpus.txt

# Output shows:
#   Orthogonality: 0.95 (very different!)
#   → Your training data may not match intended use case
```

### Example 2: Tuning Generation Parameters

```bash
# Test different temperatures
for temp in 0.5 0.7 1.0 1.2; do
  python your_model.py --temp $temp > output_temp_${temp}.txt
  python3 src/llm_analyzer.py output_temp_${temp}.txt -r reference.txt \
    > analysis_temp_${temp}.txt
done

# Compare health scores to find optimal temperature
```

### Example 3: A/B Testing Prompts

```bash
# Generate with prompt A
python your_model.py --prompt "Style A" > output_A.txt

# Generate with prompt B
python your_model.py --prompt "Style B" > output_B.txt

# Compare
python3 src/llm_analyzer.py output_A.txt -r human_baseline.txt
python3 src/llm_analyzer.py output_B.txt -r human_baseline.txt

# Choose prompt with higher health score
```

### Example 4: Continuous Quality Monitoring

```bash
#!/bin/bash
# Monitor LLM quality over time

DATE=$(date +%Y%m%d)

# Generate daily samples
python your_model.py --generate 1000 > daily_output_${DATE}.txt

# Analyze
python3 src/llm_analyzer.py daily_output_${DATE}.txt \
  -r human_baseline.txt \
  -o daily_analysis_${DATE}.json

# Extract health score
HEALTH=$(jq '.health_score' daily_analysis_${DATE}.json)

echo "$DATE,$HEALTH" >> health_scores.csv

# Alert if score drops
if [ $HEALTH -lt 70 ]; then
  echo "WARNING: Health score dropped to $HEALTH"
  # Send alert...
fi
```

## Integration with Your LLM

### Python Integration

```python
from llm_analyzer import LLMAnalyzer

# Initialize with reference corpus
analyzer = LLMAnalyzer(reference_corpus_path='human_baseline.txt')

# Generate text with your model
llm_output = your_model.generate(prompt="Write about...")

# Analyze
analysis = analyzer.analyze_llm_output(llm_output)

# Check health
if analysis['health_score'] < 70:
    print(f"⚠ Warning: Low quality output (score: {analysis['health_score']})")
    for issue in analysis['issues']:
        print(f"  - {issue['type']}: {issue['description']}")

    # Regenerate with different parameters
    llm_output = your_model.generate(
        prompt="Write about...",
        temperature=1.0,  # Increased
        no_repeat_ngram_size=3  # Added
    )

    # Re-analyze
    analysis = analyzer.analyze_llm_output(llm_output)
```

### Automatic Parameter Tuning

```python
def auto_tune_generation(model, prompt, analyzer, max_attempts=5):
    """
    Automatically tune generation parameters for best quality
    """
    best_score = 0
    best_output = None
    best_params = None

    # Try different parameter combinations
    for temp in [0.7, 0.9, 1.1]:
        for top_p in [0.8, 0.9, 0.95]:
            output = model.generate(
                prompt=prompt,
                temperature=temp,
                top_p=top_p
            )

            analysis = analyzer.analyze_llm_output(output)

            if analysis['health_score'] > best_score:
                best_score = analysis['health_score']
                best_output = output
                best_params = {'temperature': temp, 'top_p': top_p}

    return best_output, best_params, best_score

# Use it
output, params, score = auto_tune_generation(
    model=my_llm,
    prompt="Write about technology...",
    analyzer=analyzer
)

print(f"Best output (score {score}) with {params}")
```

## Advanced Use Cases

### 1. Fine-Tuning Validation

After fine-tuning, check if model quality improved:

```bash
# Before fine-tuning
python base_model.py --generate 1000 > before_finetune.txt
python3 src/llm_analyzer.py before_finetune.txt -r target_corpus.txt

# After fine-tuning
python finetuned_model.py --generate 1000 > after_finetune.txt
python3 src/llm_analyzer.py after_finetune.txt -r target_corpus.txt

# Compare:
# - Orthogonality should decrease (closer to target)
# - Health score should increase
# - Issues should be resolved
```

### 2. Domain Adaptation Testing

Check if your model adapted to new domain:

```bash
# Generate in new domain
python your_model.py --domain medical > medical_output.txt

# Compare to medical corpus
python3 src/llm_analyzer.py medical_output.txt -r medical_corpus.txt

# Low orthogonality = successful adaptation
# High orthogonality = need more training
```

### 3. Prompt Engineering

Find prompts that elicit best output:

```bash
# Test many prompts
for prompt in "${PROMPTS[@]}"; do
  python your_model.py --prompt "$prompt" > output_${i}.txt
  python3 src/llm_analyzer.py output_${i}.txt -r reference.txt \
    | grep "Health Score" >> prompt_scores.txt
done

# Choose prompt with highest score
```

## Output Format

### Console Output

Human-readable report with:
- Basic metrics (vocab size, transitions, density)
- Health score (0-100)
- Issues list with severity and recommendations
- Comparison to reference (if provided)

### JSON Output

Detailed analysis for programmatic use:

```json
{
  "text_name": "LLM Output",
  "vocabulary_size": 20,
  "total_tokens": 44,
  "transitions": 39,
  "health_score": 50,
  "issues": [
    {
      "type": "severe_mode_collapse",
      "severity": "critical",
      "description": "Severely limited vocabulary: only 20 unique words",
      "recommendation": "Increase temperature, use top-p/top-k sampling"
    }
  ],
  "comparison": {
    "orthogonality": 1.0,
    "similarity_score": 0.0,
    "assessment": "very different"
  }
}
```

## Tips

1. **Use reference corpus**: Always provide `-r reference.txt` for meaningful comparison
2. **Collect baselines**: Build reference from high-quality human text in your domain
3. **Monitor trends**: Track health scores over time to catch degradation
4. **Combine metrics**: Don't rely on single metric - look at full picture
5. **Iterate**: Use recommendations to improve parameters

## Limitations

- **First-order model**: Only considers immediate word transitions (not full context)
- **Doesn't check facts**: Only analyzes structure, not content accuracy
- **Domain-dependent**: What's "healthy" varies by domain and use case
- **Requires samples**: Needs enough text to build meaningful graph (100+ tokens)

## Next Steps

- See `LLM_CONNECTIONS.md` for theoretical background
- See `EXAMPLES.md` for more use cases
- Check `examples/` directory for sample outputs
