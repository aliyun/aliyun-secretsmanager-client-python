# coding=utf-8
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License

import json
import os


def dump(file_path, file_name, dict_obj):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + os.sep + file_name, 'w') as open_file:
        json.dump(dict_obj, open_file, indent=4, ensure_ascii=False)


def load(file_path):
    if not os.path.isfile(file_path):
        return None
    with open(file_path, 'r') as load_file:
        return json.load(load_file)
