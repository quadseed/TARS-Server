from fastapi import FastAPI, status, Response

from metadata import MetadataManager
from stream import StreamManager
from twitcasting import Twitcasting

stream_manager = StreamManager()
metadata_manager = MetadataManager()
twitcasting = Twitcasting()
app = FastAPI()


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "OK"}


@app.get("/recordings", status_code=status.HTTP_200_OK)
async def get_records():
    record_flags = stream_manager.events
    active_streams = [key for key, value in record_flags.items() if not value.is_set()]
    non_active_streams = [key for key, value in record_flags.items() if value.is_set()]
    metadata_manager.update(non_active_streams)

    response = []
    for index, live_id in enumerate(active_streams):
        user_data = metadata_manager.get(live_id)
        record = {
            "live_id": live_id,
            "user_name": user_data["user_name"],
            "live_title": user_data["live_title"],
            "live_subtitle": user_data["live_subtitle"],
            "start_time": user_data["start_time"]
        }
        response.append(record)

    return {"recordings": response}


@app.post("/recordings/{user_name}", status_code=status.HTTP_200_OK)
async def start_recording(user_name: str, response: Response):
    user_data_response = twitcasting.get_user_info(user_name)
    if user_data_response[0]:
        if user_data_response[1]["user"]["is_live"]:
            live_id = user_data_response[1]["user"]["last_movie_id"]

            live_title = "title"
            live_subtitle = "subtitle"
            live_start_time = 0

            live_data_response = twitcasting.get_movie_info(live_id)

            if live_data_response[0]:
                live_title = live_data_response[1]["movie"]["title"]
                live_subtitle = live_data_response[1]["movie"]["subtitle"]
                live_start_time = live_data_response[1]["movie"]["created"]

            if stream_manager.start(user_name, live_id, live_title, live_subtitle):
                metadata_manager.add(user_name, live_id, live_title, live_subtitle, live_start_time)
                return {
                    "live_id": live_id,
                    "user": user_name,
                    "live_title": live_title,
                    "live_subtitle": live_subtitle
                }
            else:
                response.status_code = status.HTTP_409_CONFLICT
                return {"error": "recording is on going..."}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"error": "User is offline"}
    else:
        return {"error": user_data_response[1]["error"]["message"]}


@app.delete("/recordings/{user_name}", status_code=status.HTTP_200_OK)
async def stop_recording(user_name: str, response: Response):
    user_data_response = twitcasting.get_user_info(user_name)
    if user_data_response[0]:
        if user_data_response[1]["user"]["is_live"]:
            live_id = user_data_response[1]["user"]["last_movie_id"]

            if stream_manager.stop(live_id):
                metadata_manager.remove(live_id)
                return {"user": user_name}
            else:
                response.status_code = status.HTTP_404_NOT_FOUND
                return {"error": "recording not found"}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"error": "User is offline"}
    else:
        return {"error": user_data_response[1]["error"]["message"]}


@app.get("/subscriptions", status_code=status.HTTP_200_OK)
async def get_subscriptions(response: Response):
    api_response = twitcasting.get_subscriptions()
    if api_response[0]:
        return api_response[1]
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": api_response[1]["error"]["message"]}


@app.post("/subscriptions/{user_name}", status_code=status.HTTP_200_OK)
async def add_subscription(user_name: str, response: Response):
    user_data_response = twitcasting.get_user_info(user_name)
    if user_data_response[0]:
        subscription_response = twitcasting.add_subscription(user_data_response[1]["user"]["id"])
        if subscription_response[0]:
            return subscription_response[1]
        else:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": subscription_response[1]["error"]["message"]}
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": user_data_response[1]["error"]["message"]}


@app.delete("/subscriptions/{user_name}", status_code=status.HTTP_200_OK)
async def remove_subscription(user_name: str, response: Response):
    user_data_response = twitcasting.get_user_info(user_name)
    if user_data_response[0]:
        subscription_response = twitcasting.remove_subscription(user_data_response[1]["user"]["id"])
        if subscription_response[0]:
            return subscription_response[1]
        else:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": subscription_response[1]["error"]["message"]}
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": user_data_response[1]["error"]["message"]}