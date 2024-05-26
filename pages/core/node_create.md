# クラス図

```mermaid
classDiagram
    class QualityNode {
        +nid: String
        +pid: String
        +cid: String
        +type: String
        +subtype: String
        +content: String
        +achievement: float
        +logs: List
        +fetch_all_nodes(): List
    }

    class QualityRequirement {
        +get_quality_requirements(): List
    }

    class QualityImplementation {
        +get_quality_implementations(): List
    }

    class QualityActivity {
        +task: String?
        +get_quality_activities(): List
        +get_non_achieved_activities(): List
        +dispatch(): void
    }

    class Task {
        +cost: int?
    }

    QualityNode <|-- QualityRequirement
    QualityNode <|-- QualityImplementation
    QualityNode <|-- QualityActivity
    QualityActivity <-- Task

%% +: Public（公開）
%% #: Protected（保護）
%% -: Private（非公開）