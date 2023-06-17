#Building a Camera Map

- [Map Camera Setup](#building-a-Camera-Map)
  - [Aquire and image and configure the base image](#aquire-an-image-and-corner-coordinates)
  - [Create a zone](#creating-a-zone)

## Aquire an image and corner coordinates

1. The easiest way to aquire an image and the corresponding coordinates is via [Google Mymaps](https://mymaps.google.com/).
2. From Google MyMaps, choose `Create a new map`.
3. Center your location in the screen, adjust the zoom for the maximum size.
![Initial Map Image](/images/map_guide/map_1.png)
4. Choose draw a line, then draw a line or shape.
![Create Map Image Outline](/images/map_guide/map_2.png)
5. Create an L shape around the future edge of your image, taking care to make the lines as close to a right angle as possible.
![Create Map Image Outline - step 2](/images/map_guide/map_3.png)
6. Choose the three dot menu next to the layer you created, then export as csv.
![Create Map Image Outline - step 3](/images/map_guide/map_4.png)
7. Open the csv file, in column WKT, row one, you will find a row like this.
`LINESTRING (-82.5527258 35.5410981, -82.5500865 35.5404848, -82.5504486 35.539459)`
8. From this, extract the top left and top right coordinates, this is the first and last coordinates. In this case our top left coordinate is -82.5527258 35.5410981 and our bottom right is -82.5504486 35.539459
9. Next, change the coordinates from long, latitude format, to latitude, longitude format. So the result is
    - Top Left: 35.5410981,-82.5527258
    - Bottom Right: 35.539459,-82.5504486
10. Now, take a screen shot of the image, and load the new image into your preferred image editing program, in this case I'm using GIMP.
![Create Map Image Outline - step 4](/images/map_guide/map_5.png)
11. Rotate your image until the top of the image is parralel to the line you have created.
![Create Map Image Outline - step 5](/images/map_guide/map_6.png)
12. Make sure you note the amount of rotation, and which direction, positive or negative, you applied. In this case, `-16` degrees.
![Create Map Image Outline - step 6](/images/map_guide/map_7.png)
13. Next, crop the image to the line you drew in step 5. This is the image you will use for your background image, export it and upload to your home assistant. Be sure to place it in a location that is accesible to your instance. I recommend your config folder, so `config/www/images/map.png` would be typical.
![Create Map Image Outline - step 7](/images/map_guide/map_8.png)
14. Now, find the Husqvarna Integration in Settings, Integrations, choose the gear icon.
![Create Map Image Config - step 1](/images/map_guide/map_config_1.png)
15. Choose configure.
![Create Map Image Config - step 2](/images/map_guide/map_config_2.png)
16. Choose Configure Map Camera.
![Create Map Image Config - step 3](/images/map_guide/map_config_3.png)
17. Choose the mower you to configure the camera for.
![Create Map Image Config - step 4](/images/map_guide/map_config_4.png)
18. Paste the Top Left and Bottom Right coordinates from step 9, set the rotation from step 12, and the folder you placed the image in during step 13.
![Create Map Image Config - step 5](/images/map_guide/map_config_5.png)
19. [Optional] add the home location of your mower, this will ensure the mower is always shown at home on the image if it's docked.  This prevents GPS errors, espically noticble if you have a garage causing the mower to appear to wander.
20. [Optional] If you have more than one mower, the last option is to choose additional mowers to display on this mowers map camera, choose those now.
21. Choose Submit, then finish.
22. Verify your mower is shown on the map camera properly.
![Create Map Image Config - step 6](/images/map_guide/mower_two_out.png)

## Creating a zone

1. Using [Google Mymaps](https://mymaps.google.com/) again, select the map you created in step 2.
2. Choose draw a line, then draw a line or shape around the zone you want to track, go ahead an name it.
![Create Zone - Step 1](/images/map_guide/zone_config_1.png)
3. Create additional zones and name them, using the same proccess.
4. Choose the three dot menu next to the zones you created, then export as csv.
![Create Zone - Step 2](/images/map_guide/map_4.png)
5. Open the csv file and find the polygon you created in column WKT, in this case our `Front Garden` zone is `POLYGON ((-82.552459 35.5408395, -82.5526468 35.5403331, -82.5506861 35.5398879, -82.5505225 35.5403811, -82.552459 35.5408395))`
6. Once again, we need to format it in the correct format. So our zone becomes.
`35.5408395,-82.552459; 35.5403331,-82.5526468; 35.5398879,-82.5506861; 35.5403811,-82.5505225;`
7. Note: We have to remove the last coordinate, since when you join the shape, the last coordinate is the same as the first.
8. Now, open the configure menu again.
9. Select Configure Zones.
10. Choose Create Zone.
![Create Zone - Step 3](/images/map_guide/zone_config_2.png)
11. Choose a name for your zone, in this case Front Garden, paste the zone coordinates from step 6, choose if this zone should be drawn on the map, the color for the zone, and which mowers should show the zone.
![Create Zone - Step 4](/images/map_guide/zone_config_3.png)
12. Choose Submit.
13. Now you will see your new zone, plus Create Zone and Save Zone.
![Create Zone - Step 5](/images/map_guide/zone_config_4.png)
14. You must select Save Zone, then click Submit to save the zones to the config.
15. Verify the zones are shown on the map camera.
16. Note: The Zone sensor won't update until you either reload the integration or the next update happens.




