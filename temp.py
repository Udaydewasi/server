from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import copy

client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
collection = db["users"]
collection.insert_one({"vraj":"patel"})