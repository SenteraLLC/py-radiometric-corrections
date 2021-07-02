sensor_defs = [
    {
        'criteria': {
            'Image Make': 'Sentera',
            'Image Model': '2102',
            'EXIF LensModel': '5.4mm-0001_0016'
        },
        'settings': {
            'sensor': 'D4K_NarrowNDRE',
            'cal_in_path': False,
            'independent_ils': False,
        },
        'bands': [
            ('rededge', [1.0, 0.0, -0.956]),
            ('nir', [-0.341, 0.0, 2.426])
        ]
    },
    {
        'criteria': {
            'Image Make': 'Sentera',
            'Image Model': '2102',
            'EXIF LensModel': '5.4mm-0001_0015'
        },
        'settings': {
            'sensor': 'D4K_NarrowNDVI',
            'cal_in_path': False,
            'independent_ils': False,
        },
        'bands': [
            ('red', [1.0, 0.0, -0.966]),
            ('nir', [-0.286, 0.0, 4.350])
        ]
    },
    {
        'criteria': {
            'Image Make': 'Sentera',
            'Image Model': '2102',
            'EXIF LensModel': '25.0mm-0001_0008'
        },
        'settings': {
            'sensor': 'D4K_RGB',
            'cal_in_path': False,
            'independent_ils': False,
        },
        'bands': [
            ('red', [1.0, 0.0, 0.0]),
            ('green', [0.0, 1.0, 0.0]),
            ('blue', [0.0, 0.0, 1.0])
        ]
    },
    {
        'criteria': {
            'Image Make': 'Sentera',
            'Image Model': '2102',
            'EXIF LensModel': '5.4mm-0001_0014'
        },
        'settings': {
            'sensor': 'D4K_NarrowRGB',
            'cal_in_path': False,
            'independent_ils': False,
        },
        'bands': [
            ('red', [1.0, 0.0, 0.0]),
            ('green', [0.0, 1.0, 0.0]),
            ('blue', [0.0, 0.0, 1.0])
        ]
    },
    {
        'criteria': {
            'Image Make': 'Sentera',
            'Image Model': '21214'
        },
        'settings': {
            'sensor': '6x',
            'cal_in_path': True,
            'independent_ils': True,
        }
    },
]