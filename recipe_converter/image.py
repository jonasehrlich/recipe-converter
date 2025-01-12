import io
import logging

from PIL import Image
from pillow_heif import HeifImagePlugin  # noqa: F401

_logger = logging.getLogger(__name__)


def scale_down(data: bytes, height: int | None = None, width: int | None = None) -> bytes:
    """
    Scale down an image to a given height and width.
    Only one of height or width can be given.

    :param data: The image data as bytes.
    :param height: The maximum height of the image, optional
    :param width: The maximum width of the image, optional
    :return: The scaled down image data as bytes.
    """
    if not height and not width:
        raise ValueError("At least one of height or width must be given.")
    if height and width:
        raise ValueError("Only one of height or width can be given.")

    image = Image.open(io.BytesIO(data))
    if height and image.height >= height:
        _logger.debug("Scaling down image to height %d px", height)
        return image.resize((int(image.width * height / image.height), height)).tobytes()
    if width and image.width >= width:
        _logger.debug("Scaling down image to width %d px", width)
        return image.resize((width, int(image.height * width / image.width))).tobytes()
    return data
