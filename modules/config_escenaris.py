# modules/config_escenaris.py

escenaris = [
    {
        "nom": "base_colles_mínim_de_8",
        "min_colla": 8,
        "max_colla": 20,
        "captures_per_any": [150] * 6,  # 6 anys a 150 captures fixes
        "new_hunters_per_year": (0, 0),
        "retired_hunters_per_year": (0, 0)
    },
        {
        "nom": "base_colles_mínim_de_6",
        "min_colla": 6,
        "max_colla": 20,
        "captures_per_any": [150] * 6,  # 6 anys a 150 captures fixes
        "new_hunters_per_year": (0, 0),
        "retired_hunters_per_year": (0, 0)
    },
    {
        "nom": "captures_variables_mínim_de_8",
        "min_colla": 8,
        "max_colla": 20,
        "captures_per_any": [60, 150, 100, 300, 120, 80],  # Captures variables per cada any
        "new_hunters_per_year": (0, 0),
        "retired_hunters_per_year": (0, 0)
    },
    {
        "nom": "captures_variables_mínim_de_6",
        "min_colla": 6,
        "max_colla": 20,
        "captures_per_any": [60, 150, 100, 300, 120, 80],  # Captures variables per cada any
        "new_hunters_per_year": (0, 0),
        "retired_hunters_per_year": (0, 0)
    },
    {
        "nom": "caçadors_aleatoris_mínim_de_8",
        "min_colla": 8,
        "max_colla": 20,
        "captures_per_any": [150] * 6,
        "new_hunters_per_year": (10, 100),  # Rang aleatori cada any
        "retired_hunters_per_year": (10, 100)
    },
        {
        "nom": "caçadors_aleatoris_mínim_de_6",
        "min_colla": 6,
        "max_colla": 20,
        "captures_per_any": [150] * 6,
        "new_hunters_per_year": (10, 100),  # Rang aleatori cada any
        "retired_hunters_per_year": (10, 100)
    },
    {
        "nom": "captures_variables_colles_de_8",
        "min_colla": 8,
        "max_colla": 20,
        "captures_per_any": [60, 300],
        "new_hunters_per_year": 0,
        "retired_hunters_per_year": 0
    },
        {
        "nom": "captures_variables_colles_de_6",
        "min_colla": 6,
        "max_colla": 20,
        "captures_per_any": [60, 300],
        "new_hunters_per_year": 0,
        "retired_hunters_per_year": 0
    }
]
