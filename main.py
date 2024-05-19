import logging
import logs
import os
from commands import movement_commands
from dionysus.parser import ChatResultParser
from dionysus.prompt_template import PromptTemplate
from openai import ChatCompletion, OpenAI
from image import set_user_message

robot_controller_prompt = PromptTemplate(
    identity="""You control a robot dog. You will be provided with an image taken from a forward looking camera. You choose what the next best action is.""",
    command_set=movement_commands
)

parser = ChatResultParser(movement_commands)


def get_next_action(forward_view_image_path: str) -> str:
    """Get and rune the next action to take based on the current view of the environment."""

    # load the image from "current_view.png" and pass it to the model along with the system prompt
    user_message = set_user_message("Where should we go to find the Red Ball?", file_path_list=[forward_view_image_path], max_size_px=5, tiled=True)

    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    chat_completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": robot_controller_prompt.as_system_message()},
            user_message[0],
        ],
        model="gpt-4o",
    )

    llm_response = chat_completion.choices[0].message.content

    logging.info(f"Full LLM Response\n\n{llm_response}")

    for result in parser(llm_response):
        for r in result.execute():
            pass


def run():
    get_next_action("current_view.png")


if __name__ == "__main__":
    run()