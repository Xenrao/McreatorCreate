import re

class JavaBlockParser:
    def __init__(self, content: str, block_name: str):
        self.content = content
        self.block_name = block_name
        self.simple_name = block_name.replace('Block', '')
        self.block_entity_name = block_name + 'Entity'
        self.be_registry_name = self.simple_name + 'BERegistry'

    def get_package(self):
        m = re.search(r'^package .+;$', self.content, re.MULTILINE)
        return m.group(0) if m else ''

    def get_imports(self):
        return re.findall(r'^import .+;$', self.content, re.MULTILINE)

    def get_class_body(self):
        m = re.search(rf'public class {self.block_name}.*?\{{(.*)\}}', 
                     self.content, re.DOTALL)
        return m.group(1) if m else ''

    def get_class_definition(self):
        m = re.search(rf'public class {self.block_name}.*?\{{', 
                     self.content, re.DOTALL)
        return m.group(0) if m else ''

    def has_simple_waterlogged(self):
        return 'SimpleWaterloggedBlock' in self.get_class_definition()

    def has_axis(self):
        return 'AXIS' in self.content

    def get_all_methods(self, body):
        methods = []
        lines = body.split('\n')
        i = 0
        while i < len(lines):
            method_name = self._detect_method_name(lines, i)
            if method_name:
                block, end_i = self._extract_method_block(lines, i)
                methods.append({
                    'name': method_name,
                    'lines': block,
                    'start': i,
                    'end': end_i,
                })
                i = end_i + 1
                continue
            i += 1
        return methods

    def get_tick_body(self, method_lines):
        inside = []
        brace_count = 0
        started = False
        for line in method_lines:
            if '{' in line and not started:
                started = True
                brace_count += line.count('{')
                brace_count -= line.count('}')
                continue
            if started:
                brace_count += line.count('{')
                brace_count -= line.count('}')
                if brace_count <= 0:
                    break
                inside.append(line)
        inside = [l for l in inside if l.strip() and 'super.tick' not in l]
        return inside if inside else None

    def _detect_method_name(self, lines, i):
        line = lines[i]
        check_line = line
        if '@Override' in line and i + 1 < len(lines):
            check_line = lines[i + 1]
        m = re.search(
            r'(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?'
            r'[\w<>\[\]]+\s+(\w+)\s*\(',
            check_line
        )
        return m.group(1) if m else None

    def _extract_method_block(self, lines, start):
        actual_start = start
        if start > 0 and '@Override' in lines[start - 1]:
            actual_start = start - 1
        if '@Override' in lines[start]:
            actual_start = start
        block = []
        i = actual_start
        brace_count = 0
        found_open = False
        while i < len(lines):
            line = lines[i]
            block.append(line)
            brace_count += line.count('{')
            brace_count -= line.count('}')
            if '{' in line:
                found_open = True
            if found_open and brace_count == 0:
                block.append('')
                return block, i
            i += 1
        return block, i