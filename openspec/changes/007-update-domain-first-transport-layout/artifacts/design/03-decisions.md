# Решения и Trade-offs

## Decision 1: Domain-first layout как канонический output
- Причина: alignment с архитектурой target API-проектов и contract directory structure.
- Компромисс: breaking change по путям generated файлов.

## Decision 2: `operation_id` сохраняется стабильным
- Причина: избежать каскадного breaking impact на compatibility/deprecation mechanics.
- Компромисс: идентификатор и физический layout становятся независимыми сущностями.

## Decision 3: Clean break без backward compatibility
- Причина: инструмент находится в разработке и не имеет продуктивного пользовательского следа.
- Компромисс: старые generated paths не поддерживаются как контракт.
