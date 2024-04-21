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

# Initialize FastAPI app
app = FastAPI()
translator = Translator()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    
)

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

# Define a Pydantic BaseModel for the search query
class FoodSearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "http://127.0.0.1", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# เพิ่มฟังก์ชันใหม่เพื่อดึงข้อมูล food_name2 ทั้งหมดจากฐานข้อมูล
def get_all_food_names():
    try:
        # สร้างคำสั่ง SQL เพื่อดึงข้อมูล food_name2 ทั้งหมดจากฐานข้อมูล
        sql = "SELECT DISTINCT Food_name2 FROM foods"
        mycursor.execute(sql)
        # ดึงข้อมูลทั้งหมดจากการ query
        result = mycursor.fetchall()
        # แปลงข้อมูลให้เป็น list ของ food_name2
        food_names = [item[0] for item in result]
        return food_names
    except Exception as e:
        # หากเกิดข้อผิดพลาดในการดึงข้อมูลจากฐานข้อมูล
        print("Error fetching food names:", e)
        return []

# เพิ่ม API endpoint เพื่อให้เว็บแอปพลิเคชันดึงข้อมูล food_name2 และแสดงใน dropdown หรือ autocomplete
# API เพื่อรับชื่ออาหาร
@app.get("/food_names2/")
async def get_food_names2(food_type: str):
    try:
        # สร้างคำสั่ง SQL เพื่อดึงชื่ออาหารและองค์ประกอบอาหารที่ตรงกับประเภทอาหารที่เลือก
        sql = "SELECT Food_name, Food_element FROM foods WHERE Food_element = %s"
        mycursor.execute(sql, (food_type,))
        result = mycursor.fetchall()
        food_info = [{"food_name": item[0], "food_element": item[1]} for item in result]
        return {"food_info": food_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# API เพื่อเพิ่มข้อมูลอาหารใหม่เข้าฐานข้อมูล
@app.post("/add_food/")
async def add_food(food: Food):
    # Replace invalid characters in Food_element
    food.replace_invalid_chars()

    try:
        # Insert food data into the database
        sql = "INSERT INTO foods (Food_name, Food_name2, Food_element, Food_price, Food_picture) VALUES (%s, %s, %s, %s, %s)"
        val = (food.Food_name, food.Food_name2, food.Food_element, food.Food_price, food.Food_picture)
        mycursor.execute(sql, val)
        mydb.commit()

        # Fetch the last inserted food id
        mycursor.execute("SELECT lastval()")
        last_food_id = mycursor.fetchone()[0]

        # Find matching words from dataset and Food_element
        matched_words = find_matching_words(food.Food_element)

        # Insert the matched words into foods_extraction table
        for key, words in matched_words.items():
            for word in words:
                sql = "INSERT INTO foods_extraction (food_id, food_name, food_element) VALUES (%s, %s, %s)"
                val = (last_food_id, food.Food_name, word)
                mycursor.execute(sql, val)
                mydb.commit()

        return {"message": "Food added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to find matching words from dataset
def find_matching_words(input_text):
    matched_words = {}

    for key, words in dataset.items():
        matched_words[key] = [word for word in words if re.search(word, input_text)]

    return matched_words

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

# API เพื่อค้นหาอาหารจากชื่อ
@app.get("/search_food/")
async def search_food(food_name: str):
    try:
        if not food_name.strip():  # Check if food_name is empty or whitespace
            raise HTTPException(status_code=400, detail="Food name cannot be empty")
            
        # สร้างคำสั่ง SQL เพื่อค้นหาข้อมูลอาหารจากชื่อในฐานข้อมูล
        sql = "SELECT * FROM foods WHERE Food_name ILIKE %s"
        mycursor.execute(sql, ('%' + food_name + '%',))
        result = mycursor.fetchall()
        # หากไม่พบข้อมูล
        if not result:
            raise HTTPException(status_code=404, detail="Food not found")
        # แปลงผลลัพธ์เป็นรูปแบบ JSON และส่งกลับ
        return {"food_result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    username: str
    password: str
    phone: str
    picture: str

@app.post("/register/")
async def register_user(user: UserRegistration):
    try:
        # Check if the username already exists
        sql = "SELECT * FROM users WHERE username = %s"
        mycursor.execute(sql, (user.username,))
        existing_user = mycursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Insert user data into the database
        sql = "INSERT INTO users (username, password, phone, picture) VALUES (%s, %s, %s, %s)"
        val = (user.username, user.password, user.phone, user.picture)
        mycursor.execute(sql, val)
        mydb.commit()

        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
"----------------------------------------------login-------------------------------------------------------"
# API for user login
class UserLogin(BaseModel):
    username: str
    password: str

# Define OAuth2 scheme for token generation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Your existing login endpoint
@app.post("/login/")
async def user_login(user: UserLogin):
    try:
        # Your existing login logic
        # ...

        # Generate JWT token
        expires_delta = timedelta(minutes=30)
        expires = datetime.utcnow() + expires_delta
        token_data = {"sub": user.username, "exp": expires}
        encoded_jwt = jwt.encode(token_data, "secret_key", algorithm="HS256")

        return {"access_token": encoded_jwt, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

