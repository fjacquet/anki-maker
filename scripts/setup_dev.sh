#!/bin/bash
# Development setup script for Document to Anki CLI

set -e

echo "🚀 Setting up Document to Anki CLI development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p exports
mkdir -p .cache
mkdir -p logs
mkdir -p examples/sample_documents

# Set up pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "🪝 Setting up pre-commit hooks..."
    pre-commit install
fi

# Run initial quality checks
echo "🔍 Running initial quality checks..."
uv run lint || echo "⚠️  Linting issues found - run 'uv run fix' to auto-fix"
uv run format-check || echo "⚠️  Formatting issues found - run 'uv run format' to fix"

# Create sample documents for testing
echo "📄 Creating sample documents..."
cat > examples/sample_documents/sample.txt << 'EOF'
# Sample Document for Testing

This is a sample document that can be used to test the Document to Anki CLI application.

## Key Concepts

**Photosynthesis** is the process by which plants convert light energy into chemical energy. This process occurs in the chloroplasts of plant cells and involves two main stages:

1. **Light-dependent reactions**: These occur in the thylakoids and capture light energy to produce ATP and NADPH.

2. **Light-independent reactions** (Calvin cycle): These occur in the stroma and use ATP and NADPH to convert CO2 into glucose.

## Important Facts

- Photosynthesis produces oxygen as a byproduct
- The overall equation is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2
- Chlorophyll is the primary pigment responsible for capturing light energy
- Plants are autotrophs because they can produce their own food through photosynthesis

## Study Questions

This document should generate flashcards covering:
- Definition of photosynthesis
- The two main stages of photosynthesis
- The overall chemical equation
- The role of chlorophyll
- The difference between autotrophs and heterotrophs
EOF

cat > examples/sample_documents/sample.md << 'EOF'
# Machine Learning Basics

## What is Machine Learning?

**Machine Learning** is a subset of artificial intelligence (AI) that enables computers to learn and make decisions from data without being explicitly programmed for every task.

## Types of Machine Learning

### Supervised Learning
- Uses labeled training data
- Examples: classification, regression
- Algorithms: linear regression, decision trees, neural networks

### Unsupervised Learning  
- Uses unlabeled data to find patterns
- Examples: clustering, dimensionality reduction
- Algorithms: k-means, PCA, autoencoders

### Reinforcement Learning
- Learns through interaction with environment
- Uses rewards and penalties
- Examples: game playing, robotics

## Key Terms

- **Algorithm**: A set of rules or instructions for solving a problem
- **Model**: The output of an algorithm after training on data
- **Training Data**: The dataset used to teach the algorithm
- **Feature**: An individual measurable property of observed phenomena
- **Overfitting**: When a model performs well on training data but poorly on new data

## Applications

Machine learning is used in:
- Image recognition
- Natural language processing
- Recommendation systems
- Fraud detection
- Autonomous vehicles
EOF

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Run tests: uv run test"
echo "   3. Start development: uv run dev-cli examples/sample_documents/sample.txt"
echo "   4. Or start web server: uv run dev-web"
echo ""
echo "📚 Useful commands:"
echo "   uv run test          - Run tests"
echo "   uv run test-cov      - Run tests with coverage"
echo "   uv run lint          - Check code quality"
echo "   uv run format        - Format code"
echo "   uv run quality       - Run all quality checks"
echo "   uv run dev-cli       - Run CLI in development mode"
echo "   uv run dev-web       - Run web server in development mode"
echo ""
echo "🔗 Documentation:"
echo "   README.md            - Main documentation"
echo "   examples/usage_examples.md - Usage examples"
echo "   API.md               - API documentation"