"""
@fileoverview Demo server package for AI Agent Traps red-team testing
@lastmodified 2026-04-06T18:20:21Z
@anchor DemoServer

Features: Flask web server, trap page serving, cloaking detection, exfiltration capture
Main APIs: app (Flask application instance), is_browser_request(), capture endpoint
Constraints: Localhost-only (127.0.0.1:5000), requires Flask, 1MB request body cap
Patterns: User-Agent cloaking to differentiate browsers from bots/agents

This package provides a controlled localhost demo server that serves four trap pages
implementing adversarial attack patterns from the AI Agent Traps taxonomy
(Franklin et al., 2025, Google DeepMind, SSRN-6372438). The server uses User-Agent
cloaking to serve benign content to browsers and adversarial content to automated
agents, enabling controlled red-team testing of agent defenses.

FOR AUTHORIZED DEFENSIVE SECURITY RESEARCH USE ONLY.
"""
