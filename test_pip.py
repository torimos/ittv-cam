import subprocess
import sys
import pygame
import numpy as np

def stream_video(url, target_width, target_height):
    video_width = target_width - 100  # Width of the video, accounting for button space
    video_height = target_height  # Height of the video
    command = [
        'ffmpeg',
        '-re',
        '-i', url,
        '-vf', f'scale={video_width}:{video_height}',  # This applies the scale filter
        '-f', 'image2pipe',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo', '-'
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
    
    pygame.init()
    screen = pygame.display.set_mode((target_width, target_height))
    button_rect = pygame.Rect(video_width+1, 0, 100, 50)  # Button position and size
    
    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pipe.kill()
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        print("Button clicked!")
            
            # Read frame from ffmpeg stdout
            raw_image = pipe.stdout.read(video_width * target_height * 3)
            if len(raw_image) != video_width * target_height * 3:
                print("Frame incomplete. Trying again.")
                continue
            
            image = pygame.image.fromstring(raw_image, (video_width, video_height), 'RGB')
            screen.blit(image, (0, 0), (0,0,video_width,video_height))
            
            pygame.draw.rect(screen, (255, 0, 0), button_rect)  # Draw the button
            pygame.display.flip()
    finally:
        pipe.stdout.close()
        pygame.quit()

if __name__ == "__main__":
    target_width, target_height = 1024, 600  # Change this to your desired dimensions
    stream_video("/media/rockshare/shared/Futurama (LonerD DVDRip) [NTSC]/Futurama — Volume I (LonerD DVDRip) [NTSC]/1ACV01 «Space Pilot 3000» (Космический Пилот 3000) [LonerD].mkv", target_width, target_height)
