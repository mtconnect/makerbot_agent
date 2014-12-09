#Makerbot_Driver change Log

##0.1.1
    * Preprocessors renamed to GcodeProcessor
    * GcodeProcessor Overhall:
        * Takes as input an iterable object and has a visable length
        * Outputs a list of gcodes
        * Refactored inheritance relationships to eliminate reused code
        * BundlePreprocessors eliminate multiple iterations over a single gcode file
        * All searched done with compiled state machines, speeding up text-replacements
        * Match objects passed into _transform* functions to eliminate double-work
    * Absolute imports
    * .py file name changes to match bundled python class
    * New s3g.py move function added to aid with acceleration calculations
