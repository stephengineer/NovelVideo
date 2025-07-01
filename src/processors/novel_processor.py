"""
小说处理器
整合整个小说视频生成流程
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..core import config, get_logger, db_manager
from ..services import DoubaoService, TTSService, ImageGenService, VideoGenService
from ..processors.video_processor import VideoProcessor


class NovelProcessor:
    """小说处理器类"""
    
    def __init__(self):
        self.logger = get_logger('novel_processor')
        
        # 初始化服务
        self.doubao_service = DoubaoService()
        self.tts_service = TTSService()
        self.image_gen_service = ImageGenService()
        self.video_gen_service = VideoGenService()
        self.video_processor = VideoProcessor()
    
    def process_novel(self, task_id: str, input_file: str, config_data: Dict = None) -> bool:
        """
        处理小说视频生成任务
        
        Args:
            task_id: 任务ID
            input_file: 输入小说文件路径
            config_data: 任务配置
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始处理小说视频 | 任务: {task_id} | 文件: {input_file}")
            
            # 更新任务进度
            db_manager.update_task_status(task_id, 'running', progress=0.1)
            
            # 1. 读取小说文本
            novel_text = self._read_novel_file(input_file)
            if not novel_text:
                raise Exception("无法读取小说文件")
            
            db_manager.update_task_status(task_id, 'running', progress=0.2)
            
            # 2. 分析小说，生成分镜脚本
            storyboard = self.doubao_service.analyze_novel(novel_text, task_id)
            if not storyboard:
                raise Exception("生成分镜脚本失败")
            
            # 保存分镜脚本到数据库
            self._save_storyboard_to_db(task_id, storyboard)
            
            db_manager.update_task_status(task_id, 'running', progress=0.3)
            
            # 3. 为每个场景生成素材
            scene_assets = self._generate_scene_assets(task_id, storyboard)
            if not scene_assets:
                raise Exception("生成场景素材失败")
            
            db_manager.update_task_status(task_id, 'running', progress=0.6)
            
            # 4. 合成场景视频
            scene_videos = self._create_scene_videos(task_id, scene_assets)
            if not scene_videos:
                raise Exception("合成场景视频失败")
            
            db_manager.update_task_status(task_id, 'running', progress=0.8)
            
            # 5. 合并所有场景视频
            final_video_path = self._merge_final_video(task_id, scene_videos, storyboard)
            if not final_video_path:
                raise Exception("合并最终视频失败")
            
            db_manager.update_task_status(task_id, 'running', progress=0.9)
            
            # 6. 清理临时文件
            self._cleanup_temp_files(task_id)
            
            # 7. 更新任务状态
            db_manager.update_task_status(task_id, 'completed', 
                                        output_file=final_video_path, progress=1.0)
            
            self.logger.info(f"小说视频处理完成 | 任务: {task_id} | 输出: {final_video_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"小说视频处理失败 | 任务: {task_id} | 错误: {str(e)}")
            db_manager.update_task_status(task_id, 'failed', error_message=str(e))
            return False
    
    def _read_novel_file(self, file_path: str) -> Optional[str]:
        """读取小说文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content.strip()
        except Exception as e:
            self.logger.error(f"读取小说文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def _save_storyboard_to_db(self, task_id: str, storyboard: Dict[str, Any]):
        """保存分镜脚本到数据库"""
        try:
            scenes = storyboard.get('scenes', [])
            for scene in scenes:
                db_manager.add_storyboard(
                    task_id=task_id,
                    scene_number=scene['scene_number'],
                    scene_description=scene['scene_description'],
                    duration=scene.get('duration', 15)
                )
        except Exception as e:
            self.logger.error(f"保存分镜脚本失败: {task_id}, 错误: {str(e)}")
    
    def _generate_scene_assets(self, task_id: str, storyboard: Dict[str, Any]) -> Optional[Dict[int, Dict[str, str]]]:
        """为每个场景生成素材（音频、图像、视频）"""
        try:
            scenes = storyboard.get('scenes', [])
            scene_assets = {}
            
            for scene in scenes:
                scene_number = scene['scene_number']
                scene_description = scene['scene_description']
                dialogue = scene['dialogue']
                scene_type = scene.get('scene_type', '')
                
                self.logger.info(f"生成场景素材 | 任务: {task_id} | 场景: {scene_number}")
                
                # 生成TTS音频
                audio_path = self.tts_service.generate_scene_audio(
                    scene_description, dialogue, task_id, scene_number
                )
                
                # 生成图像
                image_path = self.image_gen_service.generate_scene_image(
                    scene_description, task_id, scene_number, scene_type
                )
                
                # 生成视频
                video_path = self.video_gen_service.generate_scene_video(
                    image_path, task_id, scene_number, scene.get('duration', 15)
                )
                
                if audio_path and image_path and video_path:
                    scene_assets[scene_number] = {
                        'audio_path': audio_path,
                        'image_path': image_path,
                        'video_path': video_path,
                        'dialogue': dialogue
                    }
                    
                    # 更新数据库中的分镜脚本
                    storyboard_id = f"{task_id}_scene_{scene_number}"
                    db_manager.update_storyboard_assets(
                        storyboard_id,
                        tts_audio_path=audio_path,
                        image_path=image_path,
                        video_path=video_path
                    )
                else:
                    self.logger.error(f"场景素材生成失败 | 任务: {task_id} | 场景: {scene_number}")
                    return None
            
            return scene_assets
            
        except Exception as e:
            self.logger.error(f"生成场景素材失败 | 任务: {task_id} | 错误: {str(e)}")
            return None
    
    def _create_scene_videos(self, task_id: str, scene_assets: Dict[int, Dict[str, str]]) -> Optional[List[str]]:
        """创建场景视频（合成音频、视频和字幕）"""
        try:
            scene_videos = []
            
            for scene_number, assets in sorted(scene_assets.items()):
                self.logger.info(f"创建场景视频 | 任务: {task_id} | 场景: {scene_number}")
                
                # 生成输出路径
                output_dir = config.get_path('temp_dir') / task_id / 'final_scenes'
                output_path = output_dir / f"scene_{scene_number:02d}_final.mp4"
                
                # 创建场景视频
                success = self.video_processor.create_scene_video(
                    video_path=assets['video_path'],
                    audio_path=assets['audio_path'],
                    text_content=assets['dialogue'],
                    output_path=str(output_path),
                    task_id=task_id,
                    scene_number=scene_number
                )
                
                if success:
                    scene_videos.append(str(output_path))
                else:
                    self.logger.error(f"场景视频创建失败 | 任务: {task_id} | 场景: {scene_number}")
                    return None
            
            return scene_videos
            
        except Exception as e:
            self.logger.error(f"创建场景视频失败 | 任务: {task_id} | 错误: {str(e)}")
            return None
    
    def _merge_final_video(self, task_id: str, scene_videos: List[str], 
                          storyboard: Dict[str, Any]) -> Optional[str]:
        """合并最终视频"""
        try:
            self.logger.info(f"合并最终视频 | 任务: {task_id} | 场景数: {len(scene_videos)}")
            
            # 生成输出路径
            output_dir = config.get_path('output_dir')
            output_path = output_dir / f"{task_id}_final.mp4"
            
            # 合并场景视频
            success = self.video_processor.merge_scene_videos(
                scene_videos=scene_videos,
                output_path=str(output_path),
                task_id=task_id
            )
            
            if success:
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"合并最终视频失败 | 任务: {task_id} | 错误: {str(e)}")
            return None
    
    def _cleanup_temp_files(self, task_id: str):
        """清理临时文件"""
        try:
            temp_dir = config.get_path('temp_dir') / task_id
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                self.logger.info(f"临时文件清理完成 | 任务: {task_id}")
        except Exception as e:
            self.logger.warning(f"临时文件清理失败 | 任务: {task_id} | 错误: {str(e)}") 