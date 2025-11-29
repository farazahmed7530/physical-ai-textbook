# Implementation Plan

> **Note:** Use Context7 MCP server to fetch latest documentation for all technologies used in this project. This ensures implementations follow current best practices and API patterns.

## Phase 1: Project Setup and Core Infrastructure

- [x] 1. Initialize Docusaurus project and configure for GitHub Pages
  - [x] 1.1 Create new Docusaurus project with TypeScript template
    - Initialize project with `npx create-docusaurus@latest`
    - Configure TypeScript support
    - Set up project structure for textbook content
    - 📚 **Context7:** Use `resolve-library-id` for "docusaurus" then `get-library-docs` for latest Docusaurus setup patterns
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 Configure Docusaurus for GitHub Pages deployment
    - Update `docusaurus.config.js` with base URL and organization settings
    - Configure static asset handling
    - Set up custom domain if needed
    - 📚 **Context7:** Fetch latest GitHub Pages deployment docs from Docusaurus
    - _Requirements: 1.2, 10.2_
  - [ ]* 1.3 Write property test for navigation consistency
    - **Property 1: Navigation Consistency Across Pages**
    - **Validates: Requirements 1.3**

- [x] 2. Set up FastAPI backend project structure
  - [x] 2.1 Initialize FastAPI project with dependencies
    - Create project with Poetry/pip for dependency management
    - Install FastAPI, uvicorn, pydantic, python-dotenv
    - Set up project structure (routers, services, models, utils)
    - 📚 **Context7:** Use `resolve-library-id` for "fastapi" then `get-library-docs` for latest FastAPI project structure and best practices
    - _Requirements: 5.1, 5.4_
  - [x] 2.2 Configure CORS and middleware
    - Set up CORS for Docusaurus frontend origin
    - Add request logging middleware
    - Configure error handling middleware
    - 📚 **Context7:** Fetch latest FastAPI middleware and CORS configuration patterns
    - _Requirements: 5.1, 5.3_
  - [ ]* 2.3 Write property test for API response format
    - **Property 9: API Response Format Validity**
    - **Validates: Requirements 5.1**
  - [ ]* 2.4 Write property test for input validation
    - **Property 10: Input Validation and Error Handling**
    - **Validates: Requirements 5.2, 5.3**

- [x] 3. Set up database connections
  - [x] 3.1 Configure Neon PostgreSQL connection
    - Set up connection pooling with asyncpg
    - Create database models with SQLAlchemy
    - Implement connection health checks
    - 📚 **Context7:** Use `resolve-library-id` for "sqlalchemy" and "asyncpg" then fetch latest async database patterns
    - _Requirements: 5.4, 6.5_
  - [x] 3.2 Configure Qdrant Cloud connection
    - Install qdrant-client
    - Set up collection with proper vector dimensions (1536)
    - Implement connection verification
    - 📚 **Context7:** Use `resolve-library-id` for "qdrant" then `get-library-docs` for latest Qdrant client setup and collection management
    - _Requirements: 4.1, 5.4_
  - [x] 3.3 Create database migration scripts
    - Write SQL migrations for users, sessions, chat_messages tables
    - Write migrations for personalized_content, translated_content tables
    - Set up migration runner
    - _Requirements: 6.5_

- [x] 4. Checkpoint - Ensure infrastructure is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: Textbook Content Structure

- [x] 5. Create textbook content structure and chapters
  - [x] 5.1 Set up chapter organization and navigation
    - Create docs folder structure for chapters
    - Configure sidebar navigation in sidebars.js
    - Set up chapter ordering and categories
    - _Requirements: 2.1, 2.3_
  - [x] 5.2 Create initial chapter templates with MDX support
    - Create MDX templates with code blocks, diagrams support
    - Set up Mermaid diagram integration
    - Configure syntax highlighting for code examples
    - _Requirements: 2.2, 2.4_
  - [ ]* 5.3 Write property test for chapter content completeness
    - **Property 2: Chapter Content Completeness**
    - **Validates: Requirements 2.2**
  - [ ]* 5.4 Write property test for sequential navigation
    - **Property 3: Sequential Chapter Navigation**
    - **Validates: Requirements 2.3**
  - [ ]* 5.5 Write property test for markdown rendering
    - **Property 4: Markdown Rendering Fidelity**
    - **Validates: Requirements 2.4**

- [x] 6. Write Physical AI & Humanoid Robotics course content
  - [x] 6.1 Write Introduction and Fundamentals chapters
    - Chapter 1: Introduction to Physical AI
    - Chapter 2: Fundamentals of Humanoid Robotics
    - Chapter 3: Sensors and Perception
    - _Requirements: 2.1, 2.2_
  - [x] 6.2 Write Core Concepts chapters
    - Chapter 4: Motion Planning and Control
    - Chapter 5: Computer Vision for Robotics
    - Chapter 6: Natural Language Interaction
    - _Requirements: 2.1, 2.2_
  - [x] 6.3 Write Advanced Topics chapters
    - Chapter 7: Reinforcement Learning for Robotics
    - Chapter 8: Human-Robot Interaction
    - Chapter 9: Safety and Ethics in Physical AI
    - _Requirements: 2.1, 2.2_
  - [x] 6.4 Write Practical Applications chapters
    - Chapter 10: Building Your First Robot Project
    - Chapter 11: Industry Applications
    - Chapter 12: Future of Physical AI
    - _Requirements: 2.1, 2.2_

## Phase 3: Content Indexing and RAG Pipeline

- [x] 7. Implement content indexing system
  - [x] 7.1 Create content parser and chunker
    - Implement markdown/MDX parser to extract text
    - Create semantic chunker with 500 token chunks, 50 token overlap
    - Extract metadata (chapter_id, section_title, page_url)
    - _Requirements: 4.1_
  - [x] 7.2 Implement embedding generation service
    - Set up OpenAI embedding API client
    - Create batch embedding generation for efficiency
    - Handle rate limiting and retries
    - 📚 **Context7:** Use `resolve-library-id` for "openai" then `get-library-docs` for latest OpenAI embeddings API patterns
    - _Requirements: 4.1, 4.4_
  - [x] 7.3 Implement Qdrant indexer
    - Create upsert logic for content chunks
    - Implement metadata storage with vectors
    - Create re-indexing logic for content updates
    - 📚 **Context7:** Fetch latest Qdrant upsert and indexing patterns
    - _Requirements: 4.1, 4.3_
  - [ ]* 7.4 Write property test for consistent embeddings
    - **Property 7: Content Indexing with Consistent Embeddings**
    - **Validates: Requirements 4.1, 4.4**

- [x] 8. Implement RAG retrieval pipeline
  - [x] 8.1 Create query processor
    - Implement query preprocessing and embedding
    - Handle query expansion for better retrieval
    - _Requirements: 4.2_
  - [x] 8.2 Implement vector retriever
    - Create Qdrant search with top-k retrieval
    - Implement similarity threshold filtering
    - Return chunks with metadata and scores
    - _Requirements: 4.2_
  - [ ]* 8.3 Write property test for semantic search relevance
    - **Property 8: Semantic Search Relevance**
    - **Validates: Requirements 4.2**

- [x] 9. Implement RAG response generation
  - [x] 9.1 Create context builder
    - Assemble retrieved chunks into coherent context
    - Handle context window limits
    - Prioritize most relevant chunks
    - _Requirements: 3.1_
  - [x] 9.2 Implement response generator with OpenAI
    - Set up OpenAI Agents SDK integration
    - Create prompt template with citation instructions
    - Handle selected text context injection
    - 📚 **Context7:** Use `resolve-library-id` for "openai" then `get-library-docs` topic="agents" for latest OpenAI Agents SDK patterns
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 9.3 Implement fallback for no relevant results
    - Detect low relevance scores
    - Generate helpful fallback response with suggestions
    - _Requirements: 3.5_
  - [ ]* 9.4 Write property test for RAG response with citations
    - **Property 5: RAG Response Relevance with Citations**
    - **Validates: Requirements 3.1, 3.3**
  - [ ]* 9.5 Write property test for selected text context
    - **Property 6: Selected Text Context Influence**
    - **Validates: Requirements 3.2**

- [ ] 10. Checkpoint - Ensure RAG pipeline is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Chat API and Frontend Widget

- [ ] 11. Implement chat API endpoint
  - [ ] 11.1 Create chat router and endpoint
    - Implement POST /api/chat endpoint
    - Handle request validation with Pydantic
    - Integrate RAG pipeline
    - _Requirements: 5.1, 5.2_
  - [ ] 11.2 Implement chat history storage
    - Store chat messages in PostgreSQL
    - Associate with user_id if authenticated
    - _Requirements: 5.1_

- [ ] 12. Build chat widget for Docusaurus
  - [ ] 12.1 Create ChatWidget React component
    - Build chat UI with message list and input
    - Implement message sending and receiving
    - Add loading states and error handling
    - 📚 **Context7:** Use `resolve-library-id` for "react" then `get-library-docs` for latest React component patterns
    - _Requirements: 3.1_
  - [ ] 12.2 Implement text selection feature
    - Create TextSelector utility for capturing selections
    - Pass selected text to chat context
    - Show selected text in chat UI
    - _Requirements: 3.2_
  - [ ] 12.3 Integrate chat widget into Docusaurus
    - Create Docusaurus plugin/theme component
    - Add chat widget to all pages
    - Configure API endpoint connection
    - 📚 **Context7:** Fetch latest Docusaurus plugin/theme component patterns
    - _Requirements: 3.1_

## Phase 5: Authentication System (Bonus)

- [x] 13. Implement Better-Auth authentication
  - [x] 13.1 Set up Better-Auth server configuration
    - Install and configure better-auth
    - Set up JWT token handling
    - Configure session management
    - 📚 **Context7:** Use `resolve-library-id` for "better-auth" then `get-library-docs` for latest Better-Auth setup and configuration
    - _Requirements: 6.2, 6.3_
  - [x] 13.2 Implement user registration with background questions
    - Create registration endpoint with background fields
    - Validate and store user data in PostgreSQL
    - Hash passwords securely
    - _Requirements: 6.1, 6.5_
  - [x] 13.3 Implement login and logout endpoints
    - Create login endpoint with credential validation
    - Implement token generation and validation
    - Create logout endpoint with token invalidation
    - 📚 **Context7:** Fetch latest Better-Auth authentication flow patterns
    - _Requirements: 6.2, 6.3, 6.4_
  - [ ]* 13.4 Write property test for registration data persistence
    - **Property 11: User Registration Data Persistence**
    - **Validates: Requirements 6.1, 6.5**
  - [ ]* 13.5 Write property test for token lifecycle
    - **Property 12: Authentication Token Lifecycle**
    - **Validates: Requirements 6.2, 6.3**
  - [ ]* 13.6 Write property test for secure error messages
    - **Property 13: Secure Authentication Error Messages**
    - **Validates: Requirements 6.4**

- [x] 14. Build authentication UI components
  - [x] 14.1 Create login and registration forms
    - Build LoginForm component with validation
    - Build RegistrationForm with background questions
    - Add form error handling and feedback
    - _Requirements: 6.1, 6.2_
  - [x] 14.2 Create AuthProvider context
    - Implement authentication state management
    - Handle token storage and refresh
    - Provide auth hooks for components
    - _Requirements: 6.2_
  - [x] 14.3 Integrate auth UI into Docusaurus
    - Add login/register buttons to navbar
    - Create protected route wrapper
    - Show user status in header
    - _Requirements: 6.1, 6.2_

- [x] 15. Checkpoint - Ensure authentication is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Content Personalization (Bonus)

- [x] 16. Implement personalization service
  - [x] 16.1 Create profile analyzer
    - Implement logic to evaluate user background
    - Determine content complexity level (beginner/intermediate/advanced)
    - _Requirements: 7.1_
  - [x] 16.2 Implement content adapter with OpenAI
    - Create prompts for content adaptation
    - Preserve technical terms while adjusting explanations
    - Generate examples appropriate to experience level
    - _Requirements: 7.1, 7.2_
  - [x] 16.3 Implement personalization caching
    - Store personalized content in PostgreSQL
    - Implement cache retrieval logic
    - Handle cache invalidation on profile updates
    - _Requirements: 7.4_
  - [ ]* 16.4 Write property test for content adaptation
    - **Property 14: Personalization Content Adaptation**
    - **Validates: Requirements 7.1, 7.2**
  - [ ]* 16.5 Write property test for content caching
    - **Property 15: Content Caching Round-Trip**
    - **Validates: Requirements 7.4, 8.4**

- [x] 17. Build personalization UI
  - [x] 17.1 Create PersonalizeButton component
    - Build button component for chapter pages
    - Show loading state during personalization
    - Handle errors gracefully
    - _Requirements: 7.1_
  - [x] 17.2 Implement personalized content display
    - Replace chapter content with personalized version
    - Add indicator showing content is personalized
    - Provide option to view original content
    - _Requirements: 7.1, 7.2_
  - [x] 17.3 Handle missing profile data
    - Detect users without background data
    - Prompt to complete profile before personalization
    - _Requirements: 7.3_

## Phase 7: Urdu Translation (Bonus)

- [x] 18. Implement translation service
  - [x] 18.1 Create translation engine with OpenAI
    - Implement translation API call with Urdu target
    - Create prompt for technical term preservation
    - Handle transliteration of technical terms
    - 📚 **Context7:** Fetch latest OpenAI chat completion patterns for translation tasks
    - _Requirements: 8.1, 8.2_
  - [x] 18.2 Implement RTL formatting
    - Add CSS for right-to-left text direction
    - Handle mixed LTR/RTL content (code blocks)
    - Ensure proper text alignment
    - _Requirements: 8.3_
  - [x] 18.3 Implement translation caching
    - Store translated content in PostgreSQL
    - Implement cache retrieval by chapter_id
    - _Requirements: 8.4_
  - [ ]* 18.4 Write property test for Urdu translation validity
    - **Property 16: Urdu Translation Output Validity**
    - **Validates: Requirements 8.1, 8.2**
  - [ ]* 18.5 Write property test for RTL formatting
    - **Property 17: RTL Formatting Application**
    - **Validates: Requirements 8.3**

- [x] 19. Build translation UI
  - [x] 19.1 Create TranslateButton component
    - Build button component for chapter pages
    - Show loading state during translation
    - Handle errors gracefully
    - _Requirements: 8.1_
  - [x] 19.2 Implement translated content display
    - Replace chapter content with translated version
    - Apply RTL styling to container
    - Provide option to view original content
    - _Requirements: 8.1, 8.3_

## Phase 8: CI/CD and Deployment

- [x] 20. Set up GitHub Actions CI/CD
  - [x] 20.1 Create build and test workflow
    - Set up Node.js and Python environments
    - Run frontend and backend tests
    - Build Docusaurus static site
    - 📚 **Context7:** Use `resolve-library-id` for "github-actions" then `get-library-docs` for latest GitHub Actions workflow patterns
    - _Requirements: 10.1, 10.3_
  - [x] 20.2 Create deployment workflow for GitHub Pages
    - Deploy static site to GitHub Pages on main branch push
    - Configure custom domain if needed
    - _Requirements: 10.2_
  - [x] 20.3 Create backend deployment workflow
    - Deploy FastAPI to cloud provider (Vercel/Railway/Render)
    - Set up environment variables
    - Configure health checks
    - _Requirements: 10.4_
  - [x] 20.4 Create content indexing workflow
    - Trigger re-indexing on content changes
    - Run indexing script as part of deployment
    - _Requirements: 4.3_

- [x] 21. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
