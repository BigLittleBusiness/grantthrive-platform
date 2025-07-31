# Issue 2: Database Schema Design

**Title:** [TASK] Design and implement core database schema  
**Labels:** development, database, high-priority  
**Milestone:** Phase 1: Foundation  

## Description
Design and implement the core database schema for grant management, user management, and basic community features.

## Technical Requirements
- [ ] User and organization models
- [ ] Grant program and application models
- [ ] Basic community models (forums, resources)
- [ ] Proper relationships and constraints
- [ ] Migration system setup

## Definition of Done
- [ ] Database schema designed and documented
- [ ] Migration files created
- [ ] Seed data for development
- [ ] Schema documentation updated

## Core Models to Design
### User Management
- Users (with roles: applicant, council_staff, admin)
- Organizations (councils, NFPs)
- User profiles and preferences

### Grant Management
- Grant programs
- Grant applications
- Application statuses and workflows
- Supporting documents

### Community Features
- Forums and discussions
- Resources and templates
- Success stories

## Database Relationships
- Users belong to Organizations
- Grant programs belong to Organizations
- Applications belong to Users and Grant programs
- Community content linked to Users and Organizations

## Implementation Steps
1. Design ERD (Entity Relationship Diagram)
2. Create SQLAlchemy models
3. Set up Alembic migrations
4. Create seed data scripts
5. Document schema design decisions

## Dependencies
- Issue #1 (Project Setup) - requires backend setup

## Estimated Effort
- Schema design: 3-4 hours
- Model implementation: 2-3 hours
- Migration setup: 1-2 hours
- Seed data: 1-2 hours
- Documentation: 1-2 hours

**Total: 8-13 hours** 