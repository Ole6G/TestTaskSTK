from app.services.clustering import build_cluster_key, cluster_news_items


def test_build_cluster_key_normalizes_text() -> None:
    key = build_cluster_key(" Газпром ", "Москва", " Нефтегаз ")
    assert key == "газпром::москва::нефтегаз"


def test_cluster_news_groups_by_attributes_and_similarity() -> None:
    items = [
        {
            "company_name": "Газпром",
            "location": "Москва",
            "industry": "Энергетика",
            "title": "Газпром увеличил прибыль",
            "body": "Компания показала рост прибыли в этом квартале.",
        },
        {
            "company_name": "Газпром",
            "location": "Москва",
            "industry": "Энергетика",
            "title": "Рост прибыли Газпрома",
            "body": "Газпром показал рост прибыли и позитивную квартальную отчетность.",
        },
        {
            "company_name": "Газпром",
            "location": "Москва",
            "industry": "Энергетика",
            "title": "Газпром получил штраф",
            "body": "Регулятор выписал крупный штраф за нарушение.",
        },
        {
            "company_name": "Сбер",
            "location": "Москва",
            "industry": "Финансы",
            "title": "Сбер открывает новый офис",
            "body": "Компания расширяет присутствие в регионе.",
        },
    ]

    cluster_ids = cluster_news_items(items, similarity_threshold=0.4)
    assert cluster_ids[0] == cluster_ids[1]
    assert cluster_ids[0] != cluster_ids[2]
    assert cluster_ids[2] != cluster_ids[3]
