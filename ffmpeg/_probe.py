import json
import subprocess
from ._run import Error
from ._utils import convert_kwargs_to_cmd_line_args


def probe(filename, cmd='ffprobe', **kwargs):
    """Run ffprobe on the specified file and return a JSON representation of the output.

    Raises:
        :class:`ffmpeg.Error`: if ffprobe returns a non-zero exit code,
            an :class:`Error` is returned with a generic error message.
            The stderr output can be retrieved by accessing the
            ``stderr`` property of the exception.
    """
    args = [cmd, '-show_format', '-show_streams', '-of', 'json']
    args += convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise Error('ffprobe', out, err)
    return _add_stream_properties(json.loads(out.decode('utf-8')), err)


def _add_stream_properties(properties, err):
    """Parse stream properties from ffprove stderr output, and return as
    dictionary.

    Currently ffprobe does not return some attributes in the result JSON, which
    requires us to parse some attributes from the stderr output.

    This is temporary patch, because stderr output is not well defined. Proper
    patch should be sent to ffmpeg developers, to add required attributes to
    ffmpeg standard output.

    """
    for stream in properties["streams"]:
        if "codec_name" in stream and stream["codec_name"] == "jpeg2000":
            stream["lossless_wavelet_transform"] = _determine_quality(
                err, stream["index"])
    return properties


def _determine_quality(stderr_contents, stream_index):
    """
    Determine whether the wavelet transform of JPEG2000 stream was lossless.

    This is done by examining the line corresponding to the relevant stream and
    determining whether it contains the string "lossless".

    :stderr_contents: The stderr output of ffprobe.
    :stream_index: Index of the stream to be inspected.
    :returns: None if the stream is not a JPEG2000, otherwise True for lossless
              wavelet transform and False for lossy.
    """
    lines = stderr_contents.split(b"\n")
    for line in lines:
        if b"Stream #0:" + bytes(stream_index) in line:
            if b"Video: jpeg2000" in line:
                return b"lossless" in line
    return None


__all__ = ['probe']
