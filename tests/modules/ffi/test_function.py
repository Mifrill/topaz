from tests.base import BaseTopazTest
from topaz.objects.classobject import W_ClassObject
from topaz.modules.ffi.function import W_FunctionObject
from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

libm = clibffi.CDLL('libm.so')

class TestFunction(BaseTopazTest):

    def test_ensure_w_type(self, space):
        w_type_object = space.execute("FFI::Type::VOID")
        w_type_symbol = space.execute(":void")
        w_some_int = space.execute("1")
        w_unknown_type = space.execute(":int42")
        assert (W_FunctionObject.ensure_w_type(space, w_type_object)
                is w_type_object)
        assert (W_FunctionObject.ensure_w_type(space, w_type_symbol)
                is w_type_object)
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            W_FunctionObject.ensure_w_type(space, w_some_int)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            W_FunctionObject.ensure_w_type(space, w_unknown_type)

    def test_initialize_typing(self, space):
        fname = "FFI::DynamicLibrary::Symbol.new(:fname)"
        w_function = space.execute("""
        FFI::Function.new(:void, [:int8, :int16], %s, {})
        """ % fname) #didn't crash
        w_function = space.execute("""
        FFI::Function.new(FFI::Type::VOID,
                          [FFI::Type::INT8, FFI::Type::INT16], %s, {})
        """ % fname) # didn't crash
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(1, [], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Fixnum into Type"):
            space.execute("FFI::Function.new(:void, [2], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:null, [], %s, {})" % fname)
        with self.raises(space, "TypeError", "can't convert Symbol into Type"):
            space.execute("FFI::Function.new(:int32, [:array], %s, {})"
                          % fname)
        with self.raises(space, "TypeError",
                         "can't convert Fixnum into Symbol"):
            space.execute("FFI::Function.new(:void, [:uint8], 500, {})")

    def test_initialize_setvars(self, space):
        w_function = space.execute("""
        foo = FFI::DynamicLibrary::Symbol.new(:foo)
        FFI::Function.new(:int8, [:int16, :float64], foo, {})
        """)
        w_short = space.execute("FFI::Type::SHORT")
        w_double = space.execute("FFI::Type::DOUBLE")
        w_char = space.execute("FFI::Type::CHAR")
        assert w_function.arg_types_w == [w_short, w_double]
        assert w_function.w_ret_type == w_char
        assert w_function.name == 'foo'

    def test_attach_libm_pow(self, space):
        w_res = space.execute("""
        class LibraryMock
            def initialize
                local = FFI::DynamicLibrary::RTLD_LOCAL
                @ffi_libs = [FFI::DynamicLibrary.open('libm.so', local)]
            end
        end
        lib = LibraryMock.new
        oo_pow = FFI::DynamicLibrary::Symbol.new(:pow)
        func = FFI::Function.new(:float64, [:float64, :float64], oo_pow, {})
        func.attach(lib, 'power')
        (0..5).each.map { |x| lib.power(x, 2) }
        """)
        res = self.unwrap(space, w_res)
        assert [x for x in res] == [0.0, 1.0, 4.0, 9.0, 16.0, 25.0]

    def test_attach_libc_abs(self, space):
        w_res = space.execute("""
        class LibraryMock
            def initialize
                local = FFI::DynamicLibrary::RTLD_LOCAL
                @ffi_libs = [FFI::DynamicLibrary.open('libc.so.6', local)]
            end
        end
        lib = LibraryMock.new
        oo_abs = FFI::DynamicLibrary::Symbol.new(:abs)
        FFI::Function.new(:int32, [:int32], oo_abs, {}).attach(lib, 'abs')
        (-3..+3).each.map { |x| lib.abs(x) }
        """)
        assert self.unwrap(space, w_res) == [3, 2, 1, 0, 1, 2, 3]
