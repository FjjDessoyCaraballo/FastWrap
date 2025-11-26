# from langchain.tools import tool, ToolRuntime

# inventory = {
#     "gloves": 1.50,
#     "socks": 2.50,
#     "pants": 10,
#     "t-shirt": 5,
#     "console": 300,
#     "TV": 150,
#     "computer": 200,
#     "potato": 1,
#     "tomato": 0.5,
#     "pencil": 0.2,
#     "rubber": 0.25,
#     "poster": 2.5,
#     "paper ream": 4,
#     "suit": 300,
#     "car": 1000,
#     "bus": 5000,
# }

# @tool
# def check_products(product: str) -> str:
#     if product in inventory:
#         return f"We have {product} for ${inventory[product]}"
#     return f"Sorry, we won't have {product} in stock"
