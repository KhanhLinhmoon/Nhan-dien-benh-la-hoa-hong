from fastapi import FastAPI
app = FastAPI()
food_items = {
    'vietnam' : ['Pho', 'Nem'],
    'indian' : ['samosa', 'apple Pie']
}
@app.get('/get_items/{test}')
async def get_items(test):
    return food_items.get(test)