find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_MULTICARRIER gnuradio-multicarrier)

FIND_PATH(
    GR_MULTICARRIER_INCLUDE_DIRS
    NAMES gnuradio/multicarrier/api.h
    HINTS $ENV{MULTICARRIER_DIR}/include
        ${PC_MULTICARRIER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_MULTICARRIER_LIBRARIES
    NAMES gnuradio-multicarrier
    HINTS $ENV{MULTICARRIER_DIR}/lib
        ${PC_MULTICARRIER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-multicarrierTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_MULTICARRIER DEFAULT_MSG GR_MULTICARRIER_LIBRARIES GR_MULTICARRIER_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_MULTICARRIER_LIBRARIES GR_MULTICARRIER_INCLUDE_DIRS)
