# Invaders
A simple invaders shoot em up game. Use the space bar to shoot and arrow keys to move. Don't let the invaders land.
Currently, only works for Windows as the sound playing is done through winsound. There is probably a way to change that with Linux / macOS.
I did try QSoundEffect, but had issues with that also.

## To run from command line in a virtual environment
cd to the main folder and type:

`py -m venv env`

`env\Scripts\activate`

`py -m pip install -r requirements.txt`

`py -m invaders`

To deactivate environment

`deactivate`



## Resources

I have use a lot of resources from opengameart:

https://opengameart.org/content/spaceships-drakir
Thanks to Carlos Alface for the images.

https://opengameart.org/content/punkrobot
Thanks to Carlos AlLface for the images.

https://opengameart.org/content/asteroid-explosions-rocket-mine-and-laser

https://opengameart.org/content/animated-spy-bot-security-bot

https://opengameart.org/content/flare-effect-blender

https://opengameart.org/content/purple-space-ship

https://opengameart.org/content/explosion

https://opengameart.org/content/lasers-and-beams

https://wallpaperscraft.com/download/starry_sky_shine_glitter_118976/1152x864

https://pixabay.com/vectors/alien-big-eyes-monster-print-1295498/
Image by OpenClipart-Vectors from Pixabay

http://www.noiseforfun.com/2012-sound-effects/in-motion/


## Make exe

From outer Invaders folder:

pyinstaller -w -n "Invaders" --onefile invaders/\_\_main\_\_.py

