# Migration Guide: Multi-Language Configuration

This guide helps users migrate from previous versions of Document to Anki CLI that had hardcoded French flashcard generation to the new configurable language system.

## Overview of Changes

### What Changed in Version 0.1.0

- **Previous Behavior**: Flashcards were always generated in French, regardless of source document language
- **New Behavior**: Flashcards can be generated in English, French, Italian, or German
- **Default Language**: Changed from French to English
- **Configuration Method**: Language is now configurable via the `CARDLANG` environment variable

### Benefits of the New System

1. **Language Flexibility**: Choose from 4 supported languages
2. **Better Quality**: Language-specific grammar and vocabulary
3. **Cultural Appropriateness**: Context-aware content generation
4. **User Choice**: No longer locked into a single language

## Migration Scenarios

### Scenario 1: Keep Using French (Most Common)

If you want to maintain the previous behavior of generating French flashcards:

**Step 1**: Add language configuration to your `.env` file
```bash
# Add this line to your .env file
CARDLANG=french
```

**Step 2**: Verify the configuration
```bash
# Test with a sample document
document-to-anki sample.pdf --output test-french.csv
```

**Expected Result**: Flashcards will be generated in French, just like before.

### Scenario 2: Switch to English (New Default)

If you want to use the new default English language:

**Step 1**: No configuration needed (English is the default)
```bash
# Optional: Explicitly set English
CARDLANG=english
```

**Step 2**: Process your documents normally
```bash
document-to-anki document.pdf --output english-cards.csv
```

**Expected Result**: Flashcards will be generated in English with proper grammar and vocabulary.

### Scenario 3: Use Multiple Languages

If you want to generate flashcards in different languages for different documents:

**Method 1**: Change environment variable per session
```bash
# Generate French flashcards
CARDLANG=french document-to-anki french-textbook.pdf --output french-cards.csv

# Generate German flashcards  
CARDLANG=german document-to-anki german-manual.pdf --output german-cards.csv

# Generate Italian flashcards
CARDLANG=italian document-to-anki italian-article.pdf --output italian-cards.csv
```

**Method 2**: Use different .env files
```bash
# Create language-specific .env files
cp .env .env.french
cp .env .env.german
cp .env .env.italian

# Edit each file with appropriate CARDLANG setting
echo "CARDLANG=french" >> .env.french
echo "CARDLANG=german" >> .env.german  
echo "CARDLANG=italian" >> .env.italian

# Use specific .env file per session
cp .env.french .env && document-to-anki document.pdf
```

## Configuration Reference

### Supported Language Formats

| Language | Full Name | ISO Code | Example Configuration |
|----------|-----------|----------|----------------------|
| English | `english` | `en` | `CARDLANG=english` or `CARDLANG=en` |
| French | `french` | `fr` | `CARDLANG=french` or `CARDLANG=fr` |
| Italian | `italian` | `it` | `CARDLANG=italian` or `CARDLANG=it` |
| German | `german` | `de` | `CARDLANG=german` or `CARDLANG=de` |

### Configuration Methods

**Method 1**: Environment Variable (Recommended)
```bash
# In your .env file
CARDLANG=french
```

**Method 2**: Command Line Environment Variable
```bash
# For single command
CARDLANG=french document-to-anki input.pdf

# For session
export CARDLANG=french
document-to-anki input1.pdf
document-to-anki input2.pdf
```

**Method 3**: System Environment Variable
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export CARDLANG=french
```

## Quality Improvements

### Language-Specific Enhancements

The new system provides significant quality improvements over the previous hardcoded approach:

#### Grammar and Syntax
- **English**: Uses proper English grammar rules and sentence structure
- **French**: Follows French grammar, including proper use of articles and verb conjugations
- **Italian**: Implements Italian grammar rules and appropriate formality levels
- **German**: Handles German case system and compound word formation

#### Vocabulary and Terminology
- **Technical Terms**: Uses appropriate technical vocabulary for each language
- **Academic Language**: Adapts to academic writing conventions per language
- **Cultural Context**: Includes culturally relevant examples and references

#### Example Comparison

**Source Text**: "The mitochondria is the powerhouse of the cell."

**Previous System (Hardcoded French)**:
- Question: "Qu'est-ce que la mitochondrie?"
- Answer: "La mitochondrie est la centrale énergétique de la cellule."

**New System (Configurable)**:

**English** (`CARDLANG=english`):
- Question: "What is the function of mitochondria in cells?"
- Answer: "Mitochondria serve as the powerhouse of the cell, generating ATP through cellular respiration."

**French** (`CARDLANG=french`):
- Question: "Quel est le rôle des mitochondries dans la cellule?"
- Answer: "Les mitochondries constituent la centrale énergétique de la cellule, produisant l'ATP par la respiration cellulaire."

**German** (`CARDLANG=german`):
- Question: "Was ist die Funktion der Mitochondrien in Zellen?"
- Answer: "Mitochondrien dienen als Kraftwerke der Zelle und erzeugen ATP durch Zellatmung."

**Italian** (`CARDLANG=italian`):
- Question: "Qual è la funzione dei mitocondri nelle cellule?"
- Answer: "I mitocondri fungono da centrali energetiche della cellula, generando ATP attraverso la respirazione cellulare."

## Troubleshooting Migration Issues

### Common Problems and Solutions

#### Problem 1: Flashcards Still in French After Setting English
```
Issue: Set CARDLANG=english but flashcards are still in French
```

**Diagnosis Steps**:
```bash
# Check if .env file is being loaded
echo $CARDLANG

# Verify .env file content
cat .env | grep CARDLANG

# Test with explicit environment variable
CARDLANG=english document-to-anki test.pdf
```

**Solutions**:
1. Ensure `.env` file is in the correct directory (project root)
2. Restart your terminal session
3. Check for typos in the `.env` file
4. Use explicit environment variable as shown above

#### Problem 2: "Unsupported Language" Error
```
Error: Unsupported language 'francais'. Supported languages: english, en, french, fr, italian, it, german, de
```

**Solution**: Use the correct language codes
```bash
# Incorrect
CARDLANG=francais

# Correct
CARDLANG=french
# or
CARDLANG=fr
```

#### Problem 3: Mixed Language Output
```
Issue: Some flashcards in correct language, others in different language
```

**Diagnosis**: This can happen when:
- Source document contains multiple languages
- AI model occasionally generates incorrect language content

**Solutions**:
1. **Regenerate flashcards**: The system has built-in retry logic
2. **Use more specific model**: Switch from `gemini-flash` to `gemini-pro`
3. **Check source document**: Ensure source isn't mixing languages
4. **Manual editing**: Use the interactive editor to fix individual cards

#### Problem 4: Poor Quality in Non-English Languages
```
Issue: Flashcards in French/Italian/German have poor grammar or vocabulary
```

**Solutions**:
1. **Try different AI model**: Some models perform better with specific languages
   ```bash
   # In .env file
   MODEL=gemini/gemini-2.5-pro  # Instead of gemini-2.5-flash
   ```
2. **Check source document quality**: Poor source text leads to poor flashcards
3. **Use interactive editing**: Manually improve generated content
4. **Report issues**: Help improve the system by reporting language-specific problems

### Validation and Testing

#### Test Your Migration

**Step 1**: Create a test document
```bash
# Create a simple test file
echo "The water cycle involves evaporation, condensation, and precipitation." > test.txt
```

**Step 2**: Test each language
```bash
# Test English
CARDLANG=english document-to-anki test.txt --output test-en.csv

# Test French  
CARDLANG=french document-to-anki test.txt --output test-fr.csv

# Test Italian
CARDLANG=italian document-to-anki test.txt --output test-it.csv

# Test German
CARDLANG=german document-to-anki test.txt --output test-de.csv
```

**Step 3**: Verify output
```bash
# Check that flashcards are in the correct language
head -5 test-en.csv
head -5 test-fr.csv
head -5 test-it.csv
head -5 test-de.csv
```

#### Automated Testing Script

Create a migration test script:

```bash
#!/bin/bash
# migration-test.sh

echo "Testing multi-language configuration..."

# Test document
echo "Photosynthesis is the process by which plants convert sunlight into energy." > migration-test.txt

# Test each language
languages=("english" "french" "italian" "german")

for lang in "${languages[@]}"; do
    echo "Testing $lang..."
    CARDLANG=$lang document-to-anki migration-test.txt --output "test-$lang.csv" --no-preview --batch
    
    if [ $? -eq 0 ]; then
        echo "✅ $lang: SUCCESS"
    else
        echo "❌ $lang: FAILED"
    fi
done

# Cleanup
rm migration-test.txt test-*.csv

echo "Migration test complete!"
```

## Best Practices

### Recommended Workflow

1. **Choose Primary Language**: Set your most-used language in `.env`
2. **Test Configuration**: Verify with a small test document
3. **Batch Processing**: Use consistent language for related documents
4. **Quality Review**: Always review generated flashcards for accuracy
5. **Backup Settings**: Keep a backup of your working `.env` configuration

### Performance Considerations

- **Language Complexity**: Some languages may take slightly longer to process
- **Model Selection**: `gemini-pro` generally provides better quality for non-English languages
- **Batch Size**: Process smaller batches for better quality control

### Quality Assurance

1. **Review First Few Cards**: Always check the first few generated flashcards
2. **Spot Check**: Randomly review cards throughout the set
3. **Language Consistency**: Ensure all cards use the same language
4. **Cultural Appropriateness**: Verify examples and references are appropriate

## Getting Help

### Support Resources

- **Documentation**: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Configuration Guide**: [docs/CONFIGURATION.md](CONFIGURATION.md)
- **Examples**: [docs/EXAMPLES.md](EXAMPLES.md)

### Reporting Issues

When reporting language-related issues, please include:

1. **Language Configuration**: Your `CARDLANG` setting
2. **Source Document**: Type and language of source document
3. **Expected vs Actual**: What you expected vs what you got
4. **Environment**: Operating system and Python version
5. **Model Used**: Which AI model you're using

### Community Support

- Check existing issues for similar problems
- Provide clear reproduction steps
- Include sample input and output when possible
- Be specific about which language is causing issues

## Conclusion

The new multi-language configuration system provides much more flexibility and better quality than the previous hardcoded French system. With proper configuration, you can generate high-quality flashcards in your preferred language while maintaining the same ease of use you're accustomed to.

The migration process is straightforward, and the system is designed to be backward-compatible with clear error messages to guide you through any configuration issues.