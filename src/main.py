""" main.py """
import time
from pathlib import Path
from argparse import ArgumentParser, ArgumentError
from itertools import starmap
from matplotlib import pyplot as plt
from numpy import savez, array

from lucas_kanade.tracking_controller import TrackingController
from utils.contants import Constants
from yolo.helpers.camera import Camera
from yolo.yolo_controller import YoloController
from fft.fourier_controller import FourierController


class Main:
    ANGLE_LIST = [0, 90, 180, 270]
    PARSED_FILES_PATH = Path.joinpath(Path.cwd(), '..', 'assets', 'parsed')

    @classmethod
    def run(cls, video_path_list, parse=False, maneuver='DEFAULT', plot=False):

        camera_list = list(
            starmap(
                lambda angle, path: Camera(
                    str(Path.joinpath(Path.cwd(), *(path.split('/')))),
                    angle
                ),
                zip(cls.ANGLE_LIST, video_path_list)
            )
        )

        min_video_length = min(list(map(lambda c: c.frame_count, camera_list)))

        yolo = YoloController(cameras=camera_list, debug=False)
        lucas_kanade = TrackingController(debug=True)

        i = 0
        while i < min_video_length:
            try:
                i = i + Constants.NUMBER_OF_FRAMES
                cars_list = yolo.get_cameras_images()
                lucas_kanade.receiver(cars_list)

            except KeyboardInterrupt:
                break

        abstract_vehicle_list = list()

        for car in lucas_kanade.car_list:
            abstract_vehicle_list.append(
                FourierController.build_abstract_vehicle(
                    car.ID,
                    list(map(lambda c: c.x, car.positions)),
                    list(map(lambda c: c.y, car.positions))
                )
            )

        if plot:
            while True:
                plot_index = input('Enter vehicle index to be plotted (Q + Enter to exit): ')

                if plot_index.upper() == 'Q':
                    break

                try:
                    plt.plot(list(map(lambda p: p.x, lucas_kanade.car_list[int(plot_index)].positions)), label='X')
                    plt.plot(list(map(lambda p: p.y, lucas_kanade.car_list[int(plot_index)].positions)), label='Y')
                    plt.legend(loc='best')
                    plt.show()

                except TypeError:
                    print('Input value must be a integer or Q to exit')

                except IndexError:
                    print('Index out of bounds')

        if parse:
            current_parse_folder = Path.joinpath(cls.PARSED_FILES_PATH, str(time.time()).replace('.', '-'))
            current_parse_folder.mkdir(parents=True, exist_ok=True)
            for car in abstract_vehicle_list:
                savez(
                    f'{current_parse_folder}/'
                    f'{maneuver.upper()}_{str(car.vehicle_id).replace(".", "_")}.npz',
                    label=array([maneuver.upper()]),
                    x_sig=car.signal.x_sig,
                    y_sig=car.signal.y_sig
                )


if __name__ == '__main__':
    parser = ArgumentParser()

    optional_group = parser.add_argument_group('Optional Arguments')
    required_group = parser.add_argument_group('Required Arguments')

    optional_group.add_argument('--parse',
                                help='Boolean argument used to determine '
                                     'whether time series generated by the '
                                     'system should be stored for further training. '
                                     'Must inform --maneuver',
                                action='store_true')

    optional_group.add_argument('--maneuver',
                                help='Maneuver name so the parsed files may be saved properly')

    optional_group.add_argument('--plot',
                                help='Boolean argument used for plotting a time series. Must inform --plot_index',
                                action='store_true')

    required_group.add_argument('--video_path_list',
                                help='Set of paths to access the videos for processing, '
                                     'i. e.: "path/to/file/one; path/to/file/2", '
                                     '4 files are required',
                                required=True)

    args = parser.parse_args()

    if all([args.parse, args.maneuver]):

        path_list = args.video_path_list.split(';')
        if len(path_list) != 4:
            raise ArgumentError('--video_path_list must contain 4 paths')

        Main.run(
            path_list,
            parse=args.parse,
            maneuver=args.maneuver,
            plot=args.plot,
        )

    else:
        raise ArgumentError('arguments [--parse, --maneuver] are mutually inclusive')
