# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chat.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\x12\x04\x63hat\"b\n\x0b\x43hatMessage\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\x12\x1f\n\x04type\x18\x03 \x01(\x0e\x32\x11.chat.MessageType\x12\x11\n\ttimestamp\x18\x04 \x01(\x03\" \n\x0fUserListMessage\x12\r\n\x05users\x18\x01 \x03(\t\"\xa9\x01\n\x10WebSocketMessage\x12\x1f\n\x04type\x18\x01 \x01(\x0e\x32\x11.chat.MessageType\x12)\n\x0c\x63hat_message\x18\x02 \x01(\x0b\x32\x11.chat.ChatMessageH\x00\x12*\n\tuser_list\x18\x03 \x01(\x0b\x32\x15.chat.UserListMessageH\x00\x12\x12\n\x08username\x18\x04 \x01(\tH\x00\x42\t\n\x07payload*l\n\x0bMessageType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x10\n\x0c\x43HAT_MESSAGE\x10\x01\x12\r\n\tUSER_JOIN\x10\x02\x12\x0e\n\nUSER_LEAVE\x10\x03\x12\r\n\tUSER_LIST\x10\x04\x12\x10\n\x0cUSERNAME_SET\x10\x05\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _MESSAGETYPE._serialized_start=326
  _MESSAGETYPE._serialized_end=434
  _CHATMESSAGE._serialized_start=20
  _CHATMESSAGE._serialized_end=118
  _USERLISTMESSAGE._serialized_start=120
  _USERLISTMESSAGE._serialized_end=152
  _WEBSOCKETMESSAGE._serialized_start=155
  _WEBSOCKETMESSAGE._serialized_end=324
# @@protoc_insertion_point(module_scope)
