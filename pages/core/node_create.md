# クラス図

```mermaid
classDiagram
    class QualityNode {
        +int nid 
        +int pid 
        +list parents
        +list children
        +str type
        +str subtype 
        +int task 
        +float achievement
        +float contribution 
        +fetch_all_nodes(): List
        +dispatch()
    }

    class QualityRequirement {
        +str req_text
        +get_quality_requirements(): List
        +get_requirement_by_cid(): 
    }

    class QiURequirement{
        +str qiu_char
    }

    class PQRequirement{
        +str pq_char
    }

    class QualityImplementation {
        +str description
        +get_quality_implementations(): List
    }

    class Function{
        +
    }

    class Architecture{
        +
    }

    class QualityActivity {
        +bool is_manual
        +get_quality_activities(): List
        +get_non_achieved_activities(): List
        +get_bottom_req()
    }

    class Task {
        +int tid
        +int name
        +int nid
        +int cost
        +dict parameter
        +cost()
    }

    class ManualTask{
        +str assigned_to
    }

    class FuncTesting{

    }

    class NonFuncTesting{
        +cost()
    }



    QualityNode <|-- QualityRequirement
    QualityRequirement <|-- QiURequirement
    QualityRequirement <|-- PQRequirement
    QualityNode <|-- QualityImplementation
    QualityImplementation <|-- Function
    QualityImplementation <|-- Architecture
    QualityNode <|-- QualityActivity
    Task <|-- ManualTask
    ManualTask <|-- FuncTesting
    ManualTask <|-- NonFuncTesting

%% +: Public（公開）
%% #: Protected（保護）
%% -: Private（非公開）