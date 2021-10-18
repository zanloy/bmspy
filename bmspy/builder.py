# StdLib
from collections import defaultdict
import os
from typing import List, Type, Union

# Internal deps
from .health_update import HealthUpdate
from .utils import (
    alerts_markdown,
    errors_markdown,
    warnings_markdown,
)

# External deps
from slack_sdk.models.blocks import (
    Block,
    DividerBlock,
    HeaderBlock,
    PlainTextObject,
    SectionBlock,
)
from slack_sdk.models.blocks.basic_components import MarkdownTextObject, Option
from slack_sdk.models.blocks.block_elements import StaticSelectElement

class Builder:
    """Builder for Slack text blocks."""

    ICONS={
        'Healthy': ':white_check_mark:',
        'Unhealthy': ':x:',
        'Warning': ':warning:',
        'Alert': ':exclamation:',
        'Unknown': ':question:',
    }

    def details(obj: Type[HealthUpdate]) -> List[Type[Block]]:
        blocks: List[Type[Block]] = []
        if obj.healthy_str != 'Healthy':
            blocks.append(DividerBlock())
            if obj.errors:
                blocks.append(
                    SectionBlock(
                        text = MarkdownTextObject(
                            text = errors_markdown(obj.errors)
                        )
                    )
                )
            if obj.warnings:
                blocks.append(
                    SectionBlock(
                        text = MarkdownTextObject(
                            text = warnings_markdown(obj.warnings)
                        )
                    )
                )
            if obj.alerts:
                blocks.append(
                    SectionBlock(
                        text = MarkdownTextObject(
                            text = alerts_markdown(obj.alerts)
                        )
                    )
                )
        return blocks

    def health(objs: Union[HealthUpdate, List[HealthUpdate]], details: bool=False) -> List[Type[Block]]:
        # Validate
        if isinstance(objs, HealthUpdate):
            objs = [objs]
        elif isinstance(objs, list):
            for obj in objs:
                if not isinstance(obj, HealthUpdate):
                    raise ValueError('all objects passed in list must be an instance of HealthUpdate')
        else:
            raise ValueError('objs variable must be an instance of HealthUpdate or List[HealthUpdate]')

        # Collect data
        icon = Builder.ICONS.get(obj.healthy_str, ':interrobang:')
        mrkdown = f'{icon} [{obj.kind}] *{obj.name}* state: *{obj.healthy_str}*.'

        # Building blocks
        blocks: List[Type[Block]] = []
        blocks.append(
            SectionBlock(
                text = MarkdownTextObject(
                    text = mrkdown
                )
            )
        )
        if details:
            blocks.extend(Builder.details(obj))

        return blocks

    def health_overview(objs: Type[HealthUpdate]) -> List[Type[Block]]:
        """A health_overview is a one-line list of states and their counts along with a list of namespaces that are unhealthy."""

        # Build the summary text
        collection = defaultdict(lambda: [])
        for ns in objs:
            collection[ns.healthy_str].append(ns)
        statuses = []
        if len(collection['Healthy']):
            statuses.append(f'healthy({len(collection["Healthy"])})')
        if len(collection['Unhealthy']):
            statuses.append(f'unhealthy({len(collection["Unhealthy"])})')
        if len(collection['Warning']):
            statuses.append(f'warning({len(collection["Warning"])})')
        if len(collection['Alert']):
            statuses.append(f'alert({len(collection["Alert"])})')

        # Building Blocks
        blocks: List[Type[Block]] = []
        blocks.append(
            HeaderBlock(
                text = PlainTextObject(
                    text = f':medical_symbol: Overall health: {", ".join(statuses)}'
                )
            )
        )
        if len(collection['Unhealthy']):
            blocks.append(DividerBlock())
            lines: List[str] = []
            for ns in collection['Unhealthy']:
                lines.append(f"*{ns.name}*: {len(ns.errors)} errors, {len(ns.warnings)} warnings.")
            # Build SelectBlock for more details
            blocks.append(
                SectionBlock(
                    text = MarkdownTextObject(
                        text = os.linesep.join(lines)
                    ),
                    accessory = StaticSelectElement(
                        placeholder = PlainTextObject(
                            text = 'More details...'
                        ),
                        #options=[{'text':{'type':'plain_text','text':ns.name,'value':ns.name}} for ns in collection['Unhealthy']],
                        options = [Option(text=ns.name, value=ns.name) for ns in collection['Unhealthy']],
                        action_id = 'health'
                    )
                )
            )

        return blocks

    def transition_msg(obj: HealthUpdate) -> List[Type[Block]]:
        """Create a Slack message for an Update stating a state transition."""
        # Gather info
        icon = Builder.ICONS.get(obj.healthy_str, ':interrobang"')
        text = f'{icon} [{obj.kind}] {obj.name} transitioned state: {obj.previous_healthy_str} -> {obj.healthy_str}'

        # Building blocks
        blocks: List[Type[Block]] = []
        blocks.append(
            HeaderBlock(
                text = PlainTextObject(
                    text = text
                )
            )
        )
        blocks.extend(Builder.details(obj))
        return blocks
