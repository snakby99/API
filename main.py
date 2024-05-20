from fastapi import FastAPI, HTTPException, Depends, APIRouter, status ,File, UploadFile,Form
from pydantic import BaseModel, Field
import psycopg2
import re
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from googletrans import Translator
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from datetime import datetime, timezone
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from passlib.hash import bcrypt
from typing import List
import jwt
from fastapi.responses import JSONResponse
from fastapi import Query
import aiofiles
import os
import shutil


# Initialize FastAPI app
app = FastAPI()
translator = Translator()

# Connect to PostgreSQL database
mydb = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="1234",
    database="Project"
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
    allow_methods=["*"],
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
    except ImportError:
        raise HTTPException(status_code=500, detail="bcrypt module not found")
    except bcrypt.exceptions.InvalidSaltError:
        raise HTTPException(status_code=500, detail="Invalid salt")
    except bcrypt.exceptions.InvalidHashError:
        raise HTTPException(status_code=500, detail="Invalid hash")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"-------------------------------------login------------------------------------"

# API for user login
class Login(BaseModel):
    username: str
    password: str

logged_in_users = {}

# Secret key for JWT
SECRET_KEY = "your-secret-key"

# Function to generate JWT token
def create_jwt_token(user_id: int) -> str:
    # Token expiration time (e.g., 1 day)
    expire_time = datetime.utcnow() + timedelta(days=1)
    payload = {"user_id": user_id, "exp": expire_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# Create a Passlib context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API for user login
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
            if pwd_context.verify(user_input.password, stored_password_hash):
                # Update login status
                logged_in_users[user[0]] = True
                # Generate JWT token
                token = create_jwt_token(user[0], user[1], user[2], user[3], user[4], user[5], user[6])
                # Return additional user information
                return {"message": "Login successful", "token": token, "username": user[3], "picture": user[6]}
            else:
                raise HTTPException(status_code=401, detail="Invalid username or password")
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"---------------------------------------authorize---------------------------------------"

# HTTP Bearer token for authorization
bearer_scheme = HTTPBearer()


# HTTP Bearer token for authorization
bearer_scheme = HTTPBearer()

# สร้าง JWT token
def create_jwt_token(user_id: int, firstname: str, lastname: str, username: str, password: str, phone: str, picture: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "picture": picture,
        "exp": datetime.utcnow() + timedelta(minutes=15)  # เวลาหมดอายุ 15 นาทีจากขณะนี้
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# API for authorization
@app.get("/authorize/")
async def authorize(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Extract token from authorization header
        token = credentials.credentials
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # ตรวจสอบว่าข้อมูลมีอยู่ใน payload หรือไม่ และส่งกลับค่าที่เหมาะสม
        return {
            "message": "Authorization successful",
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "picture": payload.get("picture")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
"---------------------------------------logout---------------------------------------"
# API for user logout
@app.post("/logout/")
async def logout():
    try:
        # Clear all logged in users by resetting the dictionary
        logged_in_users.clear()
        return {"message": "All users logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"-------------------------------------Show data user------------------------------------"
# API for getting user information
@app.get("/user/{user_id}")
async def get_user(user_id: int):
    try:
        # Execute SQL query to fetch user data by user_id
        sql = "SELECT * FROM userss WHERE id = %s"
        mycursor.execute(sql, (user_id,))
        user = mycursor.fetchone()

        if user:
            # Return user information
            user_info = {
                "id": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "username": user[3],
                "phone": user[5],
                "picture": user[6]
            }
            return user_info
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
"---------------------------------------edit user---------------------------------------"
# API for updating user data
@app.put("/update_user/")
async def update_user(user: UserRegistration, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Hash the password with bcrypt
        hashed_password = bcrypt.hash(user.password)

        # Update user data in the database with hashed password
        sql = "UPDATE userss SET firstname = %s, lastname = %s, password = %s, phone = %s, picture = %s WHERE user_id = %s"
        val = (user.firstname, user.lastname, hashed_password, user.phone, user.picture, user_id)
        mycursor.execute(sql, val)
        mydb.commit()

        return {"message": "User data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"---------------------------------------delete user---------------------------------------"
# API for deleting user data
@app.delete("/delete_user/")
async def delete_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Delete user data from the database
        sql = "DELETE FROM userss WHERE user_id = %s"
        mycursor.execute(sql, (user_id,))
        mydb.commit()

        return {"message": "User data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"--------------------------------create shop-------------------------------"
# Function to get user id from JWT token
def get_user_id_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# HTTPBearer object for token authentication
bearer_scheme = HTTPBearer()

# API to add shop data
class ShopData(BaseModel):
    shop_name: str
    shop_location: str
    shop_phone: str
    shop_time: str 
    shop_picture: str
    shop_type: str

# Variable to store user-added shop data
added_shops = {}

# Function to check if user already added a shop
def user_added_shop(user_id: str) -> bool:
    return user_id in added_shops

# Function to check if shop already exists
def shop_exists(shop_name: str, shop_location: str) -> bool:
    sql_select = "SELECT COUNT(*) FROM shop WHERE shop_name = %s AND shop_location = %s"
    val = (shop_name, shop_location)
    mycursor.execute(sql_select, val)
    count = mycursor.fetchone()[0]
    return count > 0

@app.post("/add_shop/")
async def add_shop(shop: ShopData, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the user already added a shop
        if user_added_shop(user_id):
            raise HTTPException(status_code=400, detail="User already added a shop")

        # Add user id to shop data
        shop_data_with_user_id = shop.dict()
        shop_data_with_user_id["user_id"] = user_id

        # Check if the shop type is valid
        sql_select = "SELECT shop_type FROM shop2"
        mycursor.execute(sql_select)
        shop_types = mycursor.fetchall()
        valid_shop_types = [shop_type[0] for shop_type in shop_types]

        if shop.shop_type not in valid_shop_types:
            raise HTTPException(status_code=400, detail="Invalid shop type")
        
        # Add shop data to the database
        sql_insert = "INSERT INTO shop (shop_name, shop_location, shop_phone, shop_time, shop_picture, shop_text, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        shop_text = shop.shop_type
        val = (shop.shop_name, shop.shop_location, shop.shop_phone, shop.shop_time, shop.shop_picture, shop_text, user_id)
        mycursor.execute(sql_insert, val)
        mydb.commit()

        # Add user_id to added_shops
        added_shops[user_id] = True

        return {"message": "Shop data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"-------------------------------------Show data shop------------------------------------"
class ShopInfo(BaseModel):
    shop_id: int
    shop_name: str
    shop_location: str
    shop_phone: str
    shop_time: str
    shop_picture: str
    shop_text: str
    food_name: str
    food_price: str
    food_id: str
    food_picture: str

@app.get("/shops/", response_model=List[ShopInfo])
async def get_all_shops():
    try:
        # Execute SQL query to fetch all shop data
        sql = """
            SELECT s.*, f.Food_name, f.Food_price ,f.Food_id ,f.Food_picture
            FROM shop s
            LEFT JOIN food f ON s.shop_id = f.shop_id
        """
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
                    shop_time=shop_record[4],
                    shop_picture=shop_record[5],
                    shop_text=shop_record[6],
                    food_name=str(shop_record[8]) if shop_record[8] is not None else "",  
                    food_price=str(shop_record[9]) if shop_record[9] is not None else "",
                    food_id=str(shop_record[10]) if shop_record[10] is not None else "",
                    food_picture=str(shop_record[11]) if shop_record[11] is not None else ""  
                )
                shops.append(shop)
            return shops
        else:
            raise HTTPException(status_code=404, detail="No shops found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"-------------------------------edit shop-------------------------------"
# API for editing shop data
@app.put("/edit_shop/{shop_id}")
async def edit_shop(shop_id: int, updated_shop: ShopData, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the shop exists
        sql_check_shop = "SELECT * FROM shop WHERE shop_id = %s"
        mycursor.execute(sql_check_shop, (shop_id,))
        existing_shop = mycursor.fetchone()

        if not existing_shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        # Check if the user is the owner of the shop
        if existing_shop[7] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized to edit this shop")

        # Update shop data in the database
        sql_update_shop = "UPDATE shop SET shop_name = %s, shop_location = %s, shop_phone = %s, shop_time = %s, shop_picture = %s, shop_text = %s WHERE shop_id = %s"
        val = (updated_shop.shop_name, updated_shop.shop_location, updated_shop.shop_phone, updated_shop.shop_time, updated_shop.shop_picture, updated_shop.shop_type, shop_id)
        mycursor.execute(sql_update_shop, val)
        mydb.commit()

        return {"message": "Shop data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"-------------------------------delete shop-------------------------------"
# API for deleting shop
@app.delete("/delete_shop/{shop_id}")
async def delete_shop(shop_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the shop exists
        sql_check_shop = "SELECT * FROM shop WHERE shop_id = %s"
        mycursor.execute(sql_check_shop, (shop_id,))
        existing_shop = mycursor.fetchone()

        if not existing_shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        # Check if the user is the owner of the shop
        if existing_shop[7] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized to delete this shop")

        # Delete shop data from the database
        sql_delete_shop = "DELETE FROM shop WHERE shop_id = %s"
        mycursor.execute(sql_delete_shop, (shop_id,))
        mydb.commit()

        return {"message": "Shop deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"--------------------------------create food-------------------------------"
# Class to receive food data
class Food(BaseModel):
    Food_name: str
    Food_element: str
    Food_price: float
    Food_picture: str

# Add food data to the shop
@app.post("/add_food/")
async def add_food_to_shop(food: Food, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the user is the owner of any shop
        sql_check_shop_owner = "SELECT * FROM shop WHERE user_id = %s"
        mycursor.execute(sql_check_shop_owner, (user_id,))
        shop_owner = mycursor.fetchone()

        if not shop_owner:
            raise HTTPException(status_code=403, detail="User is not a shop owner")

        # Add shop_id to food data
        shop_id = shop_owner[0]  # Assuming the shop ID is in the first column
        food_with_shop_id = food.dict()
        food_with_shop_id["shop_id"] = shop_id

        # Add food data to the database
        sql_insert_food = "INSERT INTO food (Food_name, Food_element, Food_price, Food_picture, shop_id) VALUES (%s, %s, %s, %s, %s)"
        val = (food.Food_name, food.Food_element, food.Food_price, food.Food_picture, shop_id)
        mycursor.execute(sql_insert_food, val)
        mydb.commit()

        # Fetch the last inserted food id
        mycursor.execute("SELECT lastval()")
        last_food_id = mycursor.fetchone()[0]

        # Find matching words from dataset and Food_element
        matched_words = find_matching_words(food.Food_element)

        # Insert the matched words into foods_extraction table
        for key, words in matched_words.items():
            for word in words:
                # Check if the word already exists for the current food
                sql_check_existing = "SELECT * FROM foods_extraction WHERE food_id = %s AND food_element = %s"
                val_check_existing = (last_food_id, word)
                mycursor.execute(sql_check_existing, val_check_existing)
                existing_record = mycursor.fetchone()
                if not existing_record:  # If the word doesn't exist for the current food, insert it
                    sql = "INSERT INTO foods_extraction (food_id, food_name, food_element) VALUES (%s, %s, %s)"
                    val = (last_food_id, food.Food_name, word)
                    mycursor.execute(sql, val)
                    mydb.commit()

        return {"message": "Food data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to find matching words in the dataset
def find_matching_words(input_text):
    matched_words = {}

    for key, words in dataset.items():
        matched_words[key] = [word for word in words if re.search(word, input_text)]

    return matched_words
"---------------------------------------------hide food----------------------------------------------"
UPLOAD_FOLDER = "./image_user"

@app.post("/upload_image/")
async def upload_image(
    food_picture: UploadFile = File(...),
    Food_name: str = Form(...),
    Food_element: str = Form(...),
    Food_price: float = Form(...)
):
    try:
        # Get the filename
        filename = food_picture.filename

        # Create the file path
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Write the file to disk
        with open(file_path, "wb") as f:
            f.write(await food_picture.read())

        # Insert food data into the database
        sql = """
        INSERT INTO food (Food_name, Food_element, Food_price, Food_picture)
        VALUES (%s, %s, %s, %s)
        """
        val = (Food_name, Food_element, Food_price, file_path)
        mycursor.execute(sql, val)
        mydb.commit()

        return {"message": "Food data added successfully", "picture_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"---------------------------------------------get food----------------------------------------------"
# Add method to retrieve food names and IDs from the database
def get_food_data():
    food_data = []
    # Query to retrieve food names and IDs from the database
    sql_get_food_data = "SELECT food_id, Food_name FROM food"
    mycursor.execute(sql_get_food_data)
    result = mycursor.fetchall()
    for row in result:
        food_data.append({"food_id": row[0], "food_name": row[1]})
    return food_data

@app.get("/food_names/")
async def read_food_names():
    food_data = get_food_data()
    for food_entry in food_data:
        # Query to retrieve food elements based on food_id
        sql_get_food_element = "SELECT food_element FROM foods_extraction WHERE food_id = %s"
        mycursor.execute(sql_get_food_element, (food_entry["food_id"],))
        food_elements = mycursor.fetchall()
        
        # Combine food elements into a single string
        elements_combined = ' '.join([food_element[0] for food_element in food_elements])
        # Add food_element key to the food_entry dictionary
        food_entry["food_element"] = elements_combined

    return food_data

# Get food data from the shop by shop_id
@app.get("/get_food/")
async def get_food_from_shop(shop_id: int = Query(..., description="The ID of the shop")):
    try:
        # Retrieve food data from the database for the specified shop_id
        sql_get_food = "SELECT * FROM food WHERE shop_id = %s"
        mycursor.execute(sql_get_food, (shop_id,))
        food_data = mycursor.fetchall()

        if not food_data:
            return {"message": "No food found for the specified shop_id"}

        return {"food_data": food_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"-------------------------------------Show data food------------------------------------"

@app.get("/show_all_food/")
async def show_all_food():
    try:
        # Fetch all food data with associated shop_id
        sql_select_food = "SELECT food.*, shop.shop_id FROM food INNER JOIN shop ON food.shop_id = shop.shop_id"
        mycursor.execute(sql_select_food)
        foods = mycursor.fetchall()

        # Fetch food element data from foods_extraction table for each food
        all_foods = []
        for food in foods:
            food_dict = {
                "food_id": food[0],
                "Food_name": food[1],
                "Food_element": food[2],
                "Food_price": food[3],
                "Food_picture": food[4],
                "shop_id": food[5],  # Add shop_id from food table
                "food_elements": []
            }

            # Fetch associated food elements from foods_extraction table
            sql_select_food_elements = "SELECT food_element FROM foods_extraction WHERE food_id = %s"
            mycursor.execute(sql_select_food_elements, (food[0],))
            food_elements = mycursor.fetchall()

            for element in food_elements:
                food_dict["food_elements"].append(element[0])

            all_foods.append(food_dict)

        return all_foods
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

"-------------------------------------edit data food------------------------------------"
# Update food data in the shop
@app.put("/update_food/{food_id}")
async def update_food_in_shop(food_id: int, food: Food, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the user is the owner of any shop
        sql_check_shop_owner = "SELECT * FROM shop WHERE user_id = %s"
        mycursor.execute(sql_check_shop_owner, (user_id,))
        shop_owner = mycursor.fetchone()

        if not shop_owner:
            raise HTTPException(status_code=403, detail="User is not a shop owner")

        # Check if the food belongs to the shop owner
        sql_check_food_owner = "SELECT * FROM food WHERE food_id = %s AND shop_id = %s"
        mycursor.execute(sql_check_food_owner, (food_id, shop_owner[0]))
        existing_food = mycursor.fetchone()

        if not existing_food:
            raise HTTPException(status_code=404, detail="Food not found or does not belong to the shop owner")

        # Update food data in the database
        sql_update_food = "UPDATE food SET Food_name = %s, Food_element = %s, Food_price = %s, Food_picture = %s WHERE food_id = %s"
        val = (food.Food_name, food.Food_element, food.Food_price, food.Food_picture, food_id)
        mycursor.execute(sql_update_food, val)
        mydb.commit()

        return {"message": "Food data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"------------------------------------delete data food------------------------------------"

# Delete food data from the shop
@app.delete("/delete_food/{food_id}")
async def delete_food_from_shop(food_id: int, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Get user id from token
        user_id = get_user_id_from_token(credentials.credentials)

        # Check if the user is logged in
        if user_id not in logged_in_users:
            raise HTTPException(status_code=401, detail="User not logged in")

        # Check if the user is the owner of any shop
        sql_check_shop_owner = "SELECT * FROM shop WHERE user_id = %s"
        mycursor.execute(sql_check_shop_owner, (user_id,))
        shop_owner = mycursor.fetchone()

        if not shop_owner:
            raise HTTPException(status_code=403, detail="User is not a shop owner")

        # Check if the food belongs to the shop owner
        sql_check_food_owner = "SELECT * FROM food WHERE food_id = %s AND shop_id = %s"
        mycursor.execute(sql_check_food_owner, (food_id, shop_owner[0]))
        existing_food = mycursor.fetchone()

        if not existing_food:
            raise HTTPException(status_code=404, detail="Food not found or does not belong to the shop owner")

        # Delete food data from the database
        sql_delete_food = "DELETE FROM food WHERE food_id = %s"
        mycursor.execute(sql_delete_food, (food_id,))
        mydb.commit()

        return {"message": "Food data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    #


 


