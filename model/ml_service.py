## here we get the middleware info and process it

import time
import redis
import settings
import json
import numpy as np

from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image

# find info at: https://medium.com/@nina95dan/simple-image-classification-with-resnet-50-334366e7311a


# TODO
# Connect to Redis and assign to variable `db``
# Make use of settings.py module to get Redis settings like host, port, etc.
db = redis.Redis(       
    host = settings.REDIS_IP, 
    port = settings.REDIS_PORT, 
    db   = settings.REDIS_DB_ID
)

# TODO
# Load your ML model and assign to variable `model`
model = resnet50.ResNet50(include_top = True, weights = "imagenet")


def predict(image_name):
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    # TODO
    ## 1°img --> define a str with the route of the file and the file name, the target size is recommendation of Pablo
    ## settings upload folder is a string (the rout of the image) and the image name
    img = image.load_img(f"{settings.UPLOAD_FOLDER}{image_name}", target_size = (224, 224))
    ## 2°img --> transform to an array
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis = 0)
    ## 3°img --> apply resnet50 for preprocessing what we need with that image uploaded
    img = resnet50.preprocess_input(img)


    # Get predictions
    preds = model.predict(img)
    ## define a variable where I save the prediction of the image, and bring only the top 1, the best of the predictions
    img_predict = resnet50.decode_predictions(preds, top=1)
    ## the result is a list, within an other list, within a tupple,
    ## I need the position 0 of the first list, 0 of the second list and only position 1 and 2 of the tupple, so:
    _, class_name, pred_probability = img_predict[0][0]
    
    return class_name, float(pred_probability)


def classify_process():
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.

    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.
    """
    while True:
        # Inside this loop you should add the code to:
        #   1. Take a new job from Redis
        #   2. Run your ML model on the given data
        #   3. Store model prediction in a dict with the following shape:
        #      {
        #         "prediction": str,
        #         "score": float,
        #      }
        #   4. Store the results on Redis using the original job ID as the key
        #      so the API can match the results it gets to the original job
        #      sent
        # Hint: You should be able to successfully implement the communication
        #       code with Redis making use of functions `brpop()` and `set()`.
        # TODO


        ## db = redis, brings the 1 of the queue and brings back a string
        _, data_json = db.brpop(settings.REDIS_QUEUE) # brpop calls the first of queue and brings back name of queue and json en string, with _, I forget about the first and keep only the second part
       
        ## transform into dictionary what I get from brpop
        data_dictionary = json.loads(data_json) # here job_id and name

        ## call model
        class_name, score = predict(data_dictionary["image_name"])  # image_name comes from middleware

        ## send with middleware to redis
        prediction_dictionary = {"prediction": class_name, "score": score}

        db.set(data_dictionary["id"], json.dumps(prediction_dictionary))  # id comes from middleware

        # Don't forget to sleep for a bit at the end
        time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
