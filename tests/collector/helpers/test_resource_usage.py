# (c) Copyright IBM Corp. 2025

from unittest.mock import MagicMock, patch

from instana.collector.helpers.resource_usage import (
    ResourceUsage,
    _get_unix_resource_usage,
    _get_windows_resource_usage,
    get_resource_usage,
)


class TestResourceUsage:
    def test_resource_usage_namedtuple_defaults(self):
        """Test that ResourceUsage has proper default values"""
        usage = ResourceUsage()
        assert usage.ru_utime == 0.0
        assert usage.ru_stime == 0.0
        assert usage.ru_maxrss == 0
        assert usage.ru_ixrss == 0
        assert usage.ru_idrss == 0
        assert usage.ru_isrss == 0
        assert usage.ru_minflt == 0
        assert usage.ru_majflt == 0
        assert usage.ru_nswap == 0
        assert usage.ru_inblock == 0
        assert usage.ru_oublock == 0
        assert usage.ru_msgsnd == 0
        assert usage.ru_msgrcv == 0
        assert usage.ru_nsignals == 0
        assert usage.ru_nvcsw == 0
        assert usage.ru_nivcsw == 0

    def test_resource_usage_namedtuple_custom_values(self):
        """Test that ResourceUsage can be initialized with custom values"""
        usage = ResourceUsage(
            ru_utime=1.0,
            ru_stime=2.0,
            ru_maxrss=3,
            ru_ixrss=4,
            ru_idrss=5,
            ru_isrss=6,
            ru_minflt=7,
            ru_majflt=8,
            ru_nswap=9,
            ru_inblock=10,
            ru_oublock=11,
            ru_msgsnd=12,
            ru_msgrcv=13,
            ru_nsignals=14,
            ru_nvcsw=15,
            ru_nivcsw=16,
        )
        assert usage.ru_utime == 1.0
        assert usage.ru_stime == 2.0
        assert usage.ru_maxrss == 3
        assert usage.ru_ixrss == 4
        assert usage.ru_idrss == 5
        assert usage.ru_isrss == 6
        assert usage.ru_minflt == 7
        assert usage.ru_majflt == 8
        assert usage.ru_nswap == 9
        assert usage.ru_inblock == 10
        assert usage.ru_oublock == 11
        assert usage.ru_msgsnd == 12
        assert usage.ru_msgrcv == 13
        assert usage.ru_nsignals == 14
        assert usage.ru_nvcsw == 15
        assert usage.ru_nivcsw == 16

    @patch("platform.system", return_value="Linux")
    def test_get_resource_usage_unix(self, mock_platform):
        """Test that get_resource_usage calls _get_unix_resource_usage on Unix systems"""
        with patch(
            "instana.collector.helpers.resource_usage._get_unix_resource_usage"
        ) as mock_unix:
            mock_unix.return_value = ResourceUsage(ru_utime=1.0, ru_stime=2.0)
            result = get_resource_usage()
            mock_unix.assert_called_once()
            assert result.ru_utime == 1.0
            assert result.ru_stime == 2.0

    @patch("platform.system", return_value="Windows")
    def test_get_resource_usage_windows(self, mock_platform):
        """Test that get_resource_usage calls _get_windows_resource_usage on Windows systems"""
        with patch(
            "instana.collector.helpers.resource_usage._get_windows_resource_usage"
        ) as mock_windows:
            mock_windows.return_value = ResourceUsage(ru_utime=3.0, ru_stime=4.0)
            result = get_resource_usage()
            mock_windows.assert_called_once()
            assert result.ru_utime == 3.0
            assert result.ru_stime == 4.0

    def test_get_unix_resource_usage(self):
        """Test _get_unix_resource_usage function"""
        mock_rusage = MagicMock()
        mock_rusage.ru_utime = 1.1
        mock_rusage.ru_stime = 2.2
        mock_rusage.ru_maxrss = 3
        mock_rusage.ru_ixrss = 4
        mock_rusage.ru_idrss = 5
        mock_rusage.ru_isrss = 6
        mock_rusage.ru_minflt = 7
        mock_rusage.ru_majflt = 8
        mock_rusage.ru_nswap = 9
        mock_rusage.ru_inblock = 10
        mock_rusage.ru_oublock = 11
        mock_rusage.ru_msgsnd = 12
        mock_rusage.ru_msgrcv = 13
        mock_rusage.ru_nsignals = 14
        mock_rusage.ru_nvcsw = 15
        mock_rusage.ru_nivcsw = 16

        with patch("resource.getrusage", return_value=mock_rusage):
            with patch("resource.RUSAGE_SELF", 0):
                result = _get_unix_resource_usage()
                assert result.ru_utime == 1.1
                assert result.ru_stime == 2.2
                assert result.ru_maxrss == 3
                assert result.ru_ixrss == 4
                assert result.ru_idrss == 5
                assert result.ru_isrss == 6
                assert result.ru_minflt == 7
                assert result.ru_majflt == 8
                assert result.ru_nswap == 9
                assert result.ru_inblock == 10
                assert result.ru_oublock == 11
                assert result.ru_msgsnd == 12
                assert result.ru_msgrcv == 13
                assert result.ru_nsignals == 14
                assert result.ru_nvcsw == 15
                assert result.ru_nivcsw == 16

    @patch("psutil.Process")
    def test_get_windows_resource_usage_with_psutil(self, mock_process_class):
        """Test _get_windows_resource_usage function with psutil available"""
        # Setup mock objects
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process
        
        mock_cpu_times = MagicMock()
        mock_cpu_times.user = 1.1
        mock_cpu_times.system = 2.2
        mock_process.cpu_times.return_value = mock_cpu_times
        
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 3 * 1024  # Will be converted to KB
        mock_process.memory_info.return_value = mock_memory_info
        
        mock_io_counters = MagicMock()
        mock_io_counters.read_count = 10
        mock_io_counters.write_count = 11
        mock_process.io_counters.return_value = mock_io_counters
        
        mock_ctx_switches = MagicMock()
        mock_ctx_switches.voluntary = 15
        mock_ctx_switches.involuntary = 16
        mock_process.num_ctx_switches.return_value = mock_ctx_switches
        
        # Call the function
        result = _get_windows_resource_usage()
        
        # Verify results
        assert result.ru_utime == 1.1
        assert result.ru_stime == 2.2
        assert result.ru_maxrss == 3  # Converted from bytes to KB
        assert result.ru_ixrss == 0  # Not available on Windows
        assert result.ru_idrss == 0  # Not available on Windows
        assert result.ru_isrss == 0  # Not available on Windows
        assert result.ru_minflt == 0  # Not available on Windows
        assert result.ru_majflt == 0  # Not available on Windows
        assert result.ru_nswap == 0  # Not available on Windows
        assert result.ru_inblock == 10
        assert result.ru_oublock == 11
        assert result.ru_msgsnd == 0  # Not available on Windows
        assert result.ru_msgrcv == 0  # Not available on Windows
        assert result.ru_nsignals == 0  # Not available on Windows
        assert result.ru_nvcsw == 15
        assert result.ru_nivcsw == 16

    @patch("psutil.Process")
    def test_get_windows_resource_usage_with_missing_attributes(self, mock_process_class):
        """Test _get_windows_resource_usage function with some attributes missing"""
        # Setup mock objects
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process
        
        # CPU times with missing attributes
        mock_cpu_times = MagicMock()
        delattr(mock_cpu_times, 'user')  # Remove user attribute
        mock_cpu_times.system = 2.2
        mock_process.cpu_times.return_value = mock_cpu_times
        
        # Memory info with missing attributes
        mock_memory_info = MagicMock()
        delattr(mock_memory_info, 'rss')  # Remove rss attribute
        mock_process.memory_info.return_value = mock_memory_info
        
        # No IO counters
        mock_process.io_counters = None
        
        # No context switches
        mock_process.num_ctx_switches = None
        
        # Call the function
        result = _get_windows_resource_usage()
        
        # Verify results - should use defaults for missing attributes
        assert result.ru_utime == 0.0  # Default because 'user' is missing
        assert result.ru_stime == 2.2
        assert result.ru_maxrss == 0  # Default because 'rss' is missing
        assert result.ru_inblock == 0  # Default because io_counters is None
        assert result.ru_oublock == 0  # Default because io_counters is None
        assert result.ru_nvcsw == 0  # Default because num_ctx_switches is None
        assert result.ru_nivcsw == 0  # Default because num_ctx_switches is None

    @patch("psutil.Process", side_effect=ImportError)
    def test_get_windows_resource_usage_without_psutil(self, mock_process_class):
        """Test _get_windows_resource_usage function when psutil is not available"""
        result = _get_windows_resource_usage()
        
        # Should return default ResourceUsage with all zeros
        assert result.ru_utime == 0.0
        assert result.ru_stime == 0.0
        assert result.ru_maxrss == 0
        assert result.ru_ixrss == 0
        assert result.ru_idrss == 0
        assert result.ru_isrss == 0
        assert result.ru_minflt == 0
        assert result.ru_majflt == 0
        assert result.ru_nswap == 0
        assert result.ru_inblock == 0
        assert result.ru_oublock == 0
        assert result.ru_msgsnd == 0
        assert result.ru_msgrcv == 0
        assert result.ru_nsignals == 0
        assert result.ru_nvcsw == 0
        assert result.ru_nivcsw == 0