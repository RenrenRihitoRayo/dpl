from ipykernel.kernelbase import Kernel

class MyKernel(Kernel):
    implementation = 'MyKernel'
    implementation_version = '1.0'
    language = 'mydsl'
    language_version = '1.0'
    language_info = {
        'name': 'mydsl',
        'mimetype': 'text/plain',
        'file_extension': '.my',
    }
    banner = "My Custom DSL Kernel"

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        output = f"Echo: {code}"
        if not silent:
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
        return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=MyKernel)
