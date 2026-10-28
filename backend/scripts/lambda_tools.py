#!/usr/bin/env python3
"""Lambda Tools - Easy access to Lambda optimization tools.

This script provides a simple interface to all Lambda optimization tools.
"""

import sys
from pathlib import Path

# Add the scripts directory to the path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))


def main() -> int:
    """Main entry point for Lambda tools."""
    if len(sys.argv) < 2:
        print("🔧 Lambda Tools - FastAPI Lambda Optimization")
        print("=" * 50)
        print()
        print("Usage: python scripts/lambda_tools.py <command> [options]")
        print()
        print("Available commands:")
        print("  analyze     - Analyze package size and dependencies")
        print("  build       - Build optimized Lambda package")
        print("  layer       - Create Lambda layer")
        print("  check       - Run CI size checks")
        print("  optimize    - Run full optimization pipeline")
        print()
        print("Examples:")
        print("  python scripts/lambda_tools.py analyze")
        print("  python scripts/lambda_tools.py build --create-layer")
        print("  python scripts/lambda_tools.py check --fail-on-limit")
        print()
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    # Command mapping to reduce return statements
    command_handlers = {
        "analyze": lambda: _run_analyze(args),
        "build": lambda: _run_build(args),
        "layer": lambda: _run_layer(args),
        "check": lambda: _run_check(args),
        "optimize": lambda: _run_optimize(),
    }

    if command in command_handlers:
        return command_handlers[command]()

    print(f"❌ Unknown command: {command}")
    print("Run 'python scripts/lambda_tools.py' for help")
    return 1


def _run_analyze(args: list[str]) -> int:
    """Run analyze command."""
    from lambda_optimizer import main as analyze_main

    result = analyze_main(args)
    return result if isinstance(result, int) else 0


def _run_build(args: list[str]) -> int:
    """Run build command."""
    from build_lambda_package import main as build_main

    result = build_main(args)
    return result if isinstance(result, int) else 0


def _run_layer(args: list[str]) -> int:
    """Run layer command."""
    from build_lambda_package import main as build_main

    result = build_main([*args, "--create-layer"])
    return result if isinstance(result, int) else 0


def _run_check(args: list[str]) -> int:
    """Run check command."""
    from ci_size_check import main as check_main

    result = check_main(args)
    return result if isinstance(result, int) else 0


def _run_optimize() -> int:
    """Run full optimization pipeline."""
    print("🚀 Running full optimization pipeline...")

    # Run analyze
    print("\n1️⃣  Analyzing dependencies...")
    from lambda_optimizer import main as analyze_main

    analyze_main(["--generate-optimized", "--create-layer-script"])

    # Run build
    print("\n2️⃣  Building optimized package...")
    from build_lambda_package import main as build_main

    build_main(["--create-layer", "--create-dockerfile"])

    # Run check
    print("\n3️⃣  Running size checks...")
    from ci_size_check import main as check_main

    check_main(["--check-groups", "--fail-on-limit"])

    print("\n✅ Full optimization pipeline completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
