# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Entry point for the ADK web server.

This file instantiates the agent using the factory function and wraps it in an
App object, which is then discovered by the `adk web` command.
"""

from google.adk.apps import App
from financial_advisor.agent import create_agent

# 1. Create the agent instance using the factory function.
vetted_agent = create_agent()

# 2. Wrap the agent in an App object.
# The 'adk web' command will look for this 'root_agent' variable.
root_agent = App(
    name="financial_advisor_app",
    root_agent=vetted_agent
)