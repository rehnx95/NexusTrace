from app.extraction.contract.schemas import ExtractionResult
from app.extraction.pretrained.extractor import PretrainedFirstExtractor
from app.graph.writer import GraphWriter


class IngestionOrchestrator:
    def __init__(self, writer: GraphWriter):
        self.extractor = PretrainedFirstExtractor()
        self.writer = writer

    def run(
        self,
        case_id: str,
        documents: list[dict],
        append_mode: bool = False,
    ) -> tuple[ExtractionResult, dict]:
        result = self.extractor.extract(documents)
        write_summary = self.writer.write(
            case_id,
            result.entities,
            result.edges,
            replace=not append_mode,
        )
        return result, write_summary
