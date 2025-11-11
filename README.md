# AI Native Books Interaction

An intelligent, multi-tenant FastAPI service powering interactive learning experiences for AI-native educational content. Built to support "CoLearning Python: The AI-Driven Way" and future educational books.

## Overview

This service provides AI-powered interactions for educational books through contextual RAG (Retrieval-Augmented Generation), enabling learners to engage with content through multiple modes: conversational chat, Socratic dialogue, summarization, personalization, and translation.

## Features

### 🔐 Authentication & Multi-Tenancy
- Secure user authentication and authorization
- Multi-tenant architecture supporting multiple books
- Role-based access control per book

### 💬 Interaction Modes

#### 1. Standard Chat (Contextual RAG)
- Natural conversation about book content
- Context-aware responses based on chapters and lessons
- Semantic search across book materials

#### 2. Socratic Chat Mode
- Guided learning through questioning
- Encourages critical thinking and discovery
- Adapts difficulty based on learner responses

#### 3. Summarization
- Chapter-level summaries
- Lesson-level key takeaways
- Customizable summary depth and focus

#### 4. Personalization
- Content adapted to learner's skill level
- Examples tailored to learner's background
- Progressive difficulty adjustment

#### 5. Translation
- Multi-language support for chapters and lessons
- Context-preserving translation
- Code examples with localized comments

## Architecture

## Tech Stack

- **Framework**: FastAPI, ChatKit
- **AI**: Agentic Engine
- **DB**:
- **Authentication**:
- **Database**: PostgreSQL
- **Caching**:


## Books Supported

### Current
- **CoLearning Python: The AI-Driven Way**

### Coming Soon
- Additional AI-native educational content
- Community-contributed learning materials