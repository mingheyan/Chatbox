from chat_pb2 import User, UserList

# 创建一个用户对象
user = User(id=1, name="Dexter", email="dexter@example.com")
user.phone.append("123-456-7890")
user.phone.append("098-765-4321")

# 创建用户列表
user_list = UserList()
user_list.users.append(user)

# 序列化为二进制数据
serialized_data = user_list.SerializeToString()
print("Serialized Data:", serialized_data)

# 反序列化为对象
new_user_list = UserList()
new_user_list.ParseFromString(serialized_data)
for user in new_user_list.users:
    print(f"User ID: {user.id}, Name: {user.name}, Email: {user.email}, Phones: {user.phone}")

