Request Utilities
=================

This module provides utility functions for stream request automation and process management
in the Satori pipeline system. It is primarily used for repeatedly triggering pipeline input
through background HTTP POST requests.

It includes:

- A `ProcessManager` class to handle background workers using `multiprocessing`
- A `parse_tms` function for extracting timestamps from stream metadata

Components
----------

.. automodule:: ptgctl_pipeline.ptgctl_pipeline.utils.request
   :members:
   :undoc-members:
   :show-inheritance:
   :synopsis: Utility module for managing stream triggers

.. automodule:: ptgctl_pipeline.ptgctl_pipeline.utils.time
   :members:
   :undoc-members:
   :show-inheritance:
   :synopsis: Utility module parsing timestamps

