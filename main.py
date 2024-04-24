from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import psycopg2
import re
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from googletrans import Translator
from datetime import datetime, timedelta
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from passlib.hash import bcrypt
from typing import List

# Initialize FastAPI app
app = FastAPI()
translator = Translator()

# Connect to PostgreSQL database
mydb = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="123456789",
    database="project"
)
mycursor = mydb.cursor()

# Define Pydantic BaseModel for Food
class Food(BaseModel):
    Food_name: str
    Food_name2: str
    Food_price: float
    Food_element: str = Field(..., strip_whitespace=False)
    Food_picture: str

    # Function to replace invalid characters in Food_element
    def replace_invalid_chars(self):
        invalid_chars = {
            "\n": '',   # Remove newline characters
            "\r": '',   # Remove carriage return characters
            "\\": '',   # Remove backslashes
            # Add more invalid characters and their replacements as needed
        }
        # Replace invalid characters with valid characters
        for invalid_char, valid_char in invalid_chars.items():
            self.Food_element = self.Food_element.replace(invalid_char, valid_char)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

"---------------------------------------------data set------------------------------------------"

# Sample dataset
dataset = {
    "ผัก": [
        "กะหล่ำปลี","แตงกวา","ผักชี","ผักคะน้า","หอม","กระเทียม","พริกไทย","พริกขี้หนู","หอมแดง","หอมหัวใหญ่",
        "แครอท","มะเขือเทศ","มะนาว","มัน","เผือก","มันสัมปลัง","มันแกว","แตงไทย","พริกหยวก",
        "ถั่วลันเตา","ถัวฝักยาว","มะกูด","ใบมะกูด","ผักชีลาว","หัวปี","ฟักแฝง","มะละกอ","หัวไชท้าว",
        "เห็ดหอม","เห็ดหัวใหญ่","เห็ดหัวเล็ก","เห็ดเข็ม","กะหลัมปีม่วง","บล็อคโคลี่","พริกชี้ฟ้า",
        "คะน้า","ขิง","ข่า","ตะไขร้","มะเขือพวง","มะเขือเปราะ","มะเขือยาว","ถั่วงอก","ผักบุ้ง",
        "แขนง","ผักแข่ว","ผักบุ้ง","บวบ","พริกแห้ง","ขิง","ถั่วฝักยาว","ใบกระเพรา","พริกไทยอ่อน","พริก","พริกขีหนูสวน",
        "รากผักชี","ต้นหอม","หอมใหญ่","ใบชะพลู","ใบโหระพา","มะเขือ","ถั่วแขก","ถั่วพลู","ผัก","เม็ดมะม่วงหิมพานต์",
    ],
    "วัถุดิบ": [
        "เนื้อวัว","เนื้อเป็ด","เนื้อไก่","เนื้อบด","ไก่บด","หมูบด","หมูชิ้น","หมูสับ","ไก่สับ",
        "ซี่โครงหมู","ซี่โครงไก่","เนื้อสันคอ","เนื้อสันใน","เนื้อสันนอก","เนื้อน่องลาย","ขาหมู",
        "ขาไก่","สะโพก","อกไก่","ขาไก่","น่องไก่","ปีกไก่","ไก้หมัก","หมูหมัก","หมูต้ม","ไก่ต้ม",
        "เนื้อต้ม","กุ้ง","ปลาหมึก","หอย","ปลากระพง","ปลาแซลม่อน","ปลานิล","หอยลาย","หอยแครง",
        "หอยแมลงภู่","หอยนางรม","หมูสามชั้น","หมูกรอบ","ไก่หรอบ","หมูทอด","ไก่ทอด","ไก่ย่าง","หมูย่าง",
        "ปลาเผา","กึน","ตับ","เครื่องในไก่","ใส้หมู","คอไก่","หมูหมัก","ไก่หมัก","เนื้อหมัก","เนื้อแดง",
        "หมักหมู","หมักไก่","หมักเนื้อ","เป็ดย่าง","ไก้ต้ม","หมูต้ม","เนื้อต้ม","ปลาดทอด","ปลานึง",
        "เนื้อแดดเดียว","หอยหวาน","หอยเชล","หอยหลอด","หมู","ไก่","เนื้อ","ไข่ต้ม","ไข่ทอด","ไข่","ใบมะกรูด",
        "พริกชีฟ้าแดง","หมูหมัก","ตับหมู","ตับไก่","ปูเค็ม","ปูจืด","ปูดอง","ปูม้า","ปู","ปูดำ","กุ้งแห้ง","กุ้งทะเล",
        "หอยแคง","กรรเชียงปู","ลูกชิ้นปลา","ลูกชิ้นไก่","ลูกชิ้นหมู","ลูกชิ้นเนื้อ","ลูกเกต","มะพร้าว","สตอว์เบอรี่",
        "ปลาทูน่า","กล้วย","ปลาสำลี","มะม่วง","ถั่ว","เม็ดมะม่วง","หมึกกรอบ","ปลากรอบ",
    ],
    "เครื่องปรุง": ["น้ำมันหอย", "น้ำปลา", "น้ำตาล", "น้ำมันพืช","เกลือ","","น้ำตาล",
                "พริกไทย","น้ำปลา","กะปิ","ซอสถัวเหลือง","ถั่วเน่า","เต้าเจี้ยว","เต้าเจี้ยวญี่ปุ่น",
                "น้ำตาล","น้ำส้มสายชู","พริกป่น","พริกดองน้ำส้ม","ซอสพริก","ซ้อสมะเขือเทศ",
                "มัสตาร์ด","ซอสหอยนางรม","ซีอิ๊วดำ","น้ำปลาหอย","น้ำจิ้มบ๋วย","น้ำจิ้มสุกกี้","ซอสพริก",
                "ซอสมะเขือเทศ","มะยองเนส","ซอสโชยุ","ซอสทงคัตซึ","ซอสงาขาว",
                "น้ำสลัด","หัวกะทิ","กะทิ","น้ำจิ้มซีฟู้ด","ซีอิ๊วขาว","น้ำส้มสายชูกลั่น","น้ำพริกแกงส้ม",
                "น้ำมะขามเปียกเข้ม","ผงหมูแดง","น้ำตาลทราย","น้ำพริกแกงเผ็ด","ขิง","น้ำตาลปี๊บ","ผงปรุงรส","ซอสปรุงรส","ผงปรุงรส",
                "พริกแกง","น้ำตาลปี๊ป","ใบมะกรูด","พริกชีฟ้า","กระเทียม","ซีอิ้วขาว","ชะอม","น้ำซอสกระเพรา","นมข้นจืด","ผงกะหรี่",
                "เมล็ดสน","น้ำส้มบัลซามิก","น้ำมันมะกอก","น้ำตาลมะพร้าว","น้ำมะขามเปียก","มะขามเปียก","เกลือป่น","พริกไทยป่น",
                "เนยสด","ซอสสเต๊ก","นมสด",
                ],
}

"---------------------------------------------search------------------------------------------"

# API เพื่อค้นหาอาหารจากชื่อ
@app.get("/search_shop/")
async def search_shop(shop_name: str):
    try:
        if not shop_name.strip():  # Check if food_name is empty or whitespace
            raise HTTPException(status_code=400, detail="Shop name cannot be empty")
            
        # สร้างคำสั่ง SQL เพื่อค้นหาข้อมูลอาหารจากชื่อในฐานข้อมูล
        sql = "SELECT * FROM shop WHERE shop_name ILIKE %s"
        mycursor.execute(sql, ('%' + shop_name + '%',))
        result = mycursor.fetchall()
        # หากไม่พบข้อมูล
        if not result:
            raise HTTPException(status_code=404, detail="Shop not found")
        # แปลงผลลัพธ์เป็นรูปแบบ JSON และส่งกลับ
        return {"food_result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
"----------------------------------------------translate------------------------------------------"
class TranslationRequest(BaseModel):
    text: str

class TranslationResponse(BaseModel):
    translated_text: str

@app.post("/translate/th-en/")
async def translate_thai_to_english(request: TranslationRequest):
    translated = translator.translate(request.text, src='th', dest='en')
    return {"translated_text": translated.text}

@app.post("/translate/en-th/")
async def translate_english_to_thai(request: TranslationRequest):
    translated = translator.translate(request.text, src='en', dest='th')
    return {"translated_text": translated.text}


"---------------------------------------------------------register------------------------------------------"

# API for user registration
class UserRegistration(BaseModel):
    firstname: str
    lastname: str
    username: str
    password: str
    phone: str
    picture: str

@app.post("/register/")
async def register_user(user: UserRegistration):
    try:
        # Hash the password with bcrypt
        hashed_password = bcrypt.hash(user.password)

        # Insert user data into the database with hashed password
        sql = "INSERT INTO userss (firstname, lastname, username, password, phone, picture) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (user.firstname, user.lastname, user.username, hashed_password, user.phone, user.picture)
        mycursor.execute(sql, val)
        mydb.commit()

        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"---------------------------------------login ---------------------------------------"

# API for user login
class Login(BaseModel):
    username: str
    password: str

@app.post("/login/")
async def login(user_input: Login):
    try:
        # Execute SQL query to fetch user data by username
        sql = "SELECT * FROM userss WHERE username = %s"
        mycursor.execute(sql, (user_input.username,))
        user = mycursor.fetchone()

        if user:
            # Extract password hash from user data
            stored_password_hash = user[4]
            # Check if the stored password hash is a valid bcrypt hash
            if bcrypt.verify(user_input.password, stored_password_hash):
                return {"message": "Login successful"}
            else:
                raise HTTPException(status_code=401, detail="Invalid username or password")
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"-------------------------------------Show data user------------------------------------"
class UserData(BaseModel):
    firstname: str
    lastname: str
    username: str
    phone: str
    picture: str

# API to retrieve user data
@app.get("/user/{username}")
async def get_user(username: str):
    try:
        # Execute SQL query to fetch user data by username
        sql = "SELECT firstname, lastname, username, phone, picture FROM userss WHERE username = %s"
        mycursor.execute(sql, (username,))
        user_data = mycursor.fetchone()

        if user_data:
            # Extract user data and return
            user = UserData(
                firstname=user_data[0],
                lastname=user_data[1],
                username=user_data[2],
                phone=user_data[3],
                picture=user_data[4]
            )
            return user.dict()
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"---------------------------------------edit user---------------------------------------"
# API for editing user data
class EditUser(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    picture: Optional[str] = None

@app.put("/user/{user_id}/edit/")
async def edit_user(user_id: int, user_data: EditUser):
    try:
        # Fetch user data from the database
        sql_select = "SELECT * FROM userss WHERE user_id = %s"
        mycursor.execute(sql_select, (user_id,))
        user = mycursor.fetchone()

        if user:
            # Update user data
            updated_values = {}
            if user_data.firstname:
                updated_values['firstname'] = user_data.firstname
            if user_data.lastname:
                updated_values['lastname'] = user_data.lastname
            if user_data.password:
                hashed_password = bcrypt.hash(user_data.password)
                updated_values['password'] = hashed_password
            if user_data.phone:
                updated_values['phone'] = user_data.phone
            if user_data.picture:
                updated_values['picture'] = user_data.picture
            
            if updated_values:
                # Construct SQL query for updating user data
                sql_update = "UPDATE userss SET "
                sql_values = []
                for key, value in updated_values.items():
                    sql_values.append(f"{key} = %s")
                sql_update += ", ".join(sql_values)
                sql_update += " WHERE user_id = %s"

                # Execute SQL query to update user data
                val = list(updated_values.values())
                val.append(user_id)
                mycursor.execute(sql_update, val)
                mydb.commit()

                return {"message": "User data updated successfully"}
            else:
                return {"message": "No data provided for update"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"---------------------------------------delete user---------------------------------------"
# API for deleting user data
@app.delete("/user/{user_id}/delete/")
async def delete_user(user_id: int):
    try:
        # Check if user exists
        sql_select = "SELECT * FROM userss WHERE user_id = %s"
        mycursor.execute(sql_select, (user_id,))
        user = mycursor.fetchone()

        if user:
            # Execute SQL query to delete user
            sql_delete = "DELETE FROM userss WHERE user_id = %s"
            mycursor.execute(sql_delete, (user_id,))
            mydb.commit()

            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
"---------------------------------------logout---------------------------------------"
# API for user logout
@app.post("/logout/")
async def logout():
    try:
        # You can add any additional logout logic here if needed
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"--------------------------------create shop-------------------------------"
# API เพื่อเพิ่มข้อมูลร้านค้า
class ShopData(BaseModel):
    shop_name: str
    shop_location: str
    shop_phone: str
    shop_map: str
    shop_time: str
    shop_picture: str
    shop_type: str

# Assuming you have a function to get the current user's ID
def get_current_user_id():  
    # Example implementation:
    # return current_user.id  
    pass

@app.post("/add_shop/")
async def add_shop(shop: ShopData, user_id: int = Depends(get_current_user_id)):
    try:
        # เรียกข้อมูลประเภทร้านค้าจากตาราง shop2
        sql_select = "SELECT shop_type FROM shop2"
        mycursor.execute(sql_select)
        shop_types = mycursor.fetchall()

        # ดึงข้อมูลประเภทร้านค้าจากข้อมูลที่ดึงมา
        valid_shop_types = [shop_type[0] for shop_type in shop_types]

        # ตรวจสอบว่า shop_type ที่ให้มาถูกต้องหรือไม่
        if shop.shop_type not in valid_shop_types:
            raise HTTPException(status_code=400, detail="ประเภทร้านค้าไม่ถูกต้อง")

        # เพิ่มข้อมูลร้านค้าลงในฐานข้อมูล
        sql_insert = "INSERT INTO shop (shop_name, shop_location, shop_phone, shop_map, shop_time, shop_picture, shop_text) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        shop_text = shop.shop_type  # กำหนดค่าเริ่มต้นของ shop_text เป็น shop_type ที่เลือกไว้
        val = (shop.shop_name, shop.shop_location, shop.shop_phone, shop.shop_map, shop.shop_time, shop.shop_picture, shop_text)
        mycursor.execute(sql_insert, val)
        mydb.commit()

        return {"message": "เพิ่มข้อมูลร้านค้าเรียบร้อยแล้ว"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"-------------------------------------Show data shop------------------------------------"
# Define Pydantic model for shop data
class ShopInfo(BaseModel):
    shop_id: int
    shop_name: str
    shop_location: str
    shop_phone: str
    shop_map: str
    shop_time: str
    shop_picture: str
    shop_text: str
    user_id: int

# API to retrieve all shop data
@app.get("/shops/", response_model=List[ShopInfo])
async def get_all_shops():
    try:
        # Execute SQL query to fetch all shop data
        sql = "SELECT * FROM shop"
        mycursor.execute(sql)
        shop_data = mycursor.fetchall()

        if shop_data:
            # Extract shop data and return
            shops = []
            for shop_record in shop_data:
                shop = ShopInfo(
                    shop_id=shop_record[0],
                    shop_name=shop_record[1],
                    shop_location=shop_record[2],
                    shop_phone=shop_record[3],
                    shop_map=shop_record[4],
                    shop_time=shop_record[5],
                    shop_picture=shop_record[6],
                    shop_text=shop_record[7],
                    user_id=shop_record[8]
                )
                shops.append(shop)
            return shops
        else:
            raise HTTPException(status_code=404, detail="ไม่พบร้านค้าในระบบ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
"-------------------------------edit shop-------------------------------"
# API เพื่อแก้ไขข้อมูลร้านค้า
@app.put("/edit_shop/{shop_id}/")
async def edit_shop(shop_id: int, shop: ShopData, user_id: int):
    try:
        # ตรวจสอบว่าร้านค้าที่ต้องการแก้ไขมีอยู่ในฐานข้อมูลหรือไม่
        sql_select = "SELECT * FROM shop WHERE shop_id = %s AND user_id = %s"
        mycursor.execute(sql_select, (shop_id, user_id))
        existing_shop = mycursor.fetchone()

        if existing_shop:
            # เรียกข้อมูลประเภทร้านค้าจากตาราง shop2
            sql_select_types = "SELECT shop_type FROM shop2"
            mycursor.execute(sql_select_types)
            shop_types = mycursor.fetchall()

            # ดึงข้อมูลประเภทร้านค้าจากข้อมูลที่ดึงมา
            valid_shop_types = [shop_type[0] for shop_type in shop_types]

            # ตรวจสอบว่า shop_type ที่ให้มาถูกต้องหรือไม่
            if shop.shop_type not in valid_shop_types:
                raise HTTPException(status_code=400, detail="ประเภทร้านค้าไม่ถูกต้อง")

            # อัปเดตข้อมูลร้านค้า
            sql_update = "UPDATE shop SET shop_name = %s, shop_location = %s, shop_phone = %s, shop_map = %s, shop_time = %s, shop_picture = %s, shop_text = %s WHERE shop_id = %s AND user_id = %s"
            val = (shop.shop_name, shop.shop_location, shop.shop_phone, shop.shop_map, shop.shop_time, shop.shop_picture, shop.shop_type, shop_id, user_id)
            mycursor.execute(sql_update, val)
            mydb.commit()

            return {"message": "แก้ไขข้อมูลร้านค้าเรียบร้อยแล้ว"}
        else:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลร้านค้าที่ต้องการแก้ไขหรือไม่มีสิทธิ์ในการแก้ไขข้อมูลร้านค้านี้")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"-------------------------------delete shop-------------------------------"
# API เพื่อลบข้อมูลร้านค้า
@app.delete("/delete_shop/{shop_id}/")
async def delete_shop(shop_id: int, user_id: int):
    try:
        # ตรวจสอบว่าร้านค้าที่ต้องการลบมีอยู่ในฐานข้อมูลหรือไม่
        sql_select = "SELECT * FROM shop WHERE shop_id = %s AND user_id = %s"
        mycursor.execute(sql_select, (shop_id, user_id))
        existing_shop = mycursor.fetchone()

        if existing_shop:
            # ลบข้อมูลร้านค้า
            sql_delete = "DELETE FROM shop WHERE shop_id = %s AND user_id = %s"
            mycursor.execute(sql_delete, (shop_id, user_id))
            mydb.commit()

            return {"message": "ลบข้อมูลร้านค้าเรียบร้อยแล้ว"}
        else:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลร้านค้าที่ต้องการลบหรือไม่มีสิทธิ์ในการลบข้อมูลร้านค้านี้")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"--------------------------------create food-------------------------------"
# Model for the Food data
class Food(BaseModel):
    Food_name: str
    Food_element: str
    Food_price: float
    Food_picture: str
    Food_text2: str

    def replace_invalid_chars(self):
        # Implement logic to replace invalid characters in Food_element
        pass

# Function to retrieve existing food names from database
def get_existing_food_names():
    food_names = []
    sql_get_food_names = "SELECT DISTINCT Food_name2 FROM food"
    mycursor.execute(sql_get_food_names)
    results = mycursor.fetchall()
    for result in results:
        food_names.append(result[0])
    return food_names

# API endpoint to add food to shop
@app.post("/add_food/{shop_id}/")
async def add_food_to_shop(shop_id: int, food: Food):
    food.replace_invalid_chars()

    try:
        # Check if the shop exists
        sql_check_shop = "SELECT * FROM shop WHERE shop_id = %s"
        mycursor.execute(sql_check_shop, (shop_id,))
        shop = mycursor.fetchone()

        if shop:
            # Insert food data into the database
            sql_insert_food = "INSERT INTO food (Food_name, Food_element, Food_price, Food_picture, Food_text2, shop_id) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (food.Food_name, food.Food_element, food.Food_price, food.Food_picture, food.Food_text2, shop_id)
            mycursor.execute(sql_insert_food, val)
            mydb.commit()

            return {"message": "Food added to shop successfully"}
        else:
            raise HTTPException(status_code=404, detail="Shop not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API endpoint to get Food_element based on selected Food_name
@app.get("/get_food_element/{food_name}")
async def get_food_element(food_name: str):
    try:
        # Retrieve Food_element from the database based on Food_name
        sql_get_food_element = "SELECT Food_element FROM food WHERE Food_name = %s"
        mycursor.execute(sql_get_food_element, (food_name,))
        food_element = mycursor.fetchone()[0]

        return {"Food_element": food_element}  # Return Food_element as JSON
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

"-------------------------------------Show data food------------------------------------"


# Modify the FoodInfo model to remove Food_name2
class FoodInfo(BaseModel):
    Food_name: str
    Food_element: str
    Food_price: float
    Food_picture: str
    Food_text2: str

@app.get("/foods/", response_model=List[FoodInfo])
async def get_all_foods():
    try:
        # Fetch all food details from food table
        sql_food = "SELECT * FROM food"
        mycursor.execute(sql_food)
        food_data = mycursor.fetchall()

        if food_data:
            # Extract food data
            foods_info = []
            for food_record in food_data:
                food_info = FoodInfo(
                    Food_name=food_record[0],  # Adjust index to match the position of Food_name in the query result
                    Food_element=food_record[1],  # Adjust index to match the position of Food_element in the query result
                    Food_price=food_record[2],  # Adjust index to match the position of Food_price in the query result
                    Food_picture=food_record[3],  # Adjust index to match the position of Food_picture in the query result
                    Food_text2=food_record[4]  # Adjust index to match the position of Food_text2 in the query result
                )
                foods_info.append(food_info)
            return foods_info
        else:
            raise HTTPException(status_code=404, detail="No food items found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"-------------------------------------edit data food------------------------------------"
# API endpoint to update food data
@app.put("/update_food/{food_id}/")
async def update_food_data(food_id: int, updated_food: Food):
    updated_food.replace_invalid_chars()

    try:
        # Check if the food exists
        sql_check_food = "SELECT * FROM food WHERE food_id = %s"
        mycursor.execute(sql_check_food, (food_id,))
        existing_food = mycursor.fetchone()

        if existing_food:
            # Update food data in the database
            sql_update_food = "UPDATE food SET Food_name = %s, Food_element = %s, Food_price = %s, Food_picture = %s, Food_text2 = %s WHERE food_id = %s"
            val = (updated_food.Food_name, updated_food.Food_element, updated_food.Food_price, updated_food.Food_picture, updated_food.Food_text2, food_id)
            mycursor.execute(sql_update_food, val)
            mydb.commit()

            return {"message": "Food data updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Food not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
"-------------------------------------delte data food------------------------------------"

# API endpoint to delete food from shop
@app.delete("/delete_food/{food_id}/")
async def delete_food_from_shop(food_id: int):
    try:
        # Check if the food exists
        sql_check_food = "SELECT * FROM food WHERE food_id = %s"
        mycursor.execute(sql_check_food, (food_id,))
        existing_food = mycursor.fetchone()

        if existing_food:
            # Delete food from the database
            sql_delete_food = "DELETE FROM food WHERE food_id = %s"
            mycursor.execute(sql_delete_food, (food_id,))
            mydb.commit()

            return {"message": "Food deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Food not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


