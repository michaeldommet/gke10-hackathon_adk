#!/usr/bin/env python3
"""
Compatibility CLI for the ADK Self-Healing Agent.

Note: This agent is primarily designed to work with 'adk web'.
For full functionality, use: adk web
"""

import sys

def main():
    """Simple CLI that redirects to ADK web interface."""
    print("🤖 ADK Self-Healing Agent")
    print("=" * 40)
    print("This agent is designed to work with the ADK web interface.")
    print()
    print("To run the agent:")
    print("  adk web")
    print()
    print("To test the agent configuration:")
    print("  python test_adk_agent.py")
    print()
    print("For more information, see README.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
