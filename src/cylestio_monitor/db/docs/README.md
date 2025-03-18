# Cylestio Monitor Database Documentation

This directory contains comprehensive documentation for the Cylestio Monitor database schema and related components.

## Table of Contents

1. [Overview](./overview.md) - High-level overview of the database architecture
2. [Schema](./schema.md) - Complete database schema with ER diagrams
3. [Models](./models.md) - Detailed documentation of SQLAlchemy models
4. [Migrations](./migrations.md) - Database migration strategy
5. [Query Patterns](./query_patterns.md) - Common query patterns and examples
6. [Integration](./integration.md) - Integration guidelines for external systems

## Purpose

This documentation serves as the authoritative reference for the Cylestio Monitor database design, implementation, and usage. It is intended for both internal developers working directly with the Python codebase and external developers building integrations with other systems.

## Diagram Legend

Throughout the documentation, we use standardized ER diagrams with the following notation:

- `PK` - Primary Key
- `FK` - Foreign Key
- `UK` - Unique Key
- One-to-many relationships: `||--o{`
- One-to-one relationships: `||--||`
- Many-to-many relationships: `}o--o{`

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Database Best Practices](https://docs.cylestio.com/best-practices) (internal link) 